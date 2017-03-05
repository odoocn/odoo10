#coding:utf-8
from odoo import api, fields, models,_
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_utils


#期初数据填报
class data_fill(models.Model):
    _name='data.fill'

    name = fields.Char(
       u'盘点参考',
        readonly=True, required=True,
        states={'draft': [('readonly', False)]})
    date = fields.Datetime(
        u'盘点时间',
        readonly=True, required=True,
        default=fields.Datetime.now,
        help="The date that will be used for the stock level check of the products and the validation of the stock move related to this inventory.")
    line_ids = fields.One2many(
        'data.fill.line', 'inventory_id', string='盘点',
        copy=True, readonly=False,
        states={'done': [('readonly', True)]})
    move_ids = fields.One2many(
        'stock.move', 'inventory_id', string='创建的移动',
        states={'done': [('readonly', True)]})
    state = fields.Selection(string='状态', selection=[
        ('draft', '草稿'),
        ('cancel', '已取消'),
        ('confirm', '进行中'),
        ('done', '已验证')],
        copy=False, index=True, readonly=True,
        default='draft')
    company_id = fields.Many2one(
        'res.company', 'Company',
        readonly=True, index=True, required=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: self.env['res.company']._company_default_get('stock.inventory'))
    location_id = fields.Many2one(
        'stock.location', 'Inventoried Location',
        readonly=True, required=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: getattr(self.env.ref('stock.warehouse0', raise_if_not_found=False) or self.env['stock.warehouse'], 'lot_stock_id').id)
    product_id = fields.Many2one(
        'product.product', 'Inventoried Product',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="Specify Product to focus your inventory on a particular Product.")
    package_id = fields.Many2one(
        'stock.quant.package', 'Inventoried Pack',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="Specify Pack to focus your inventory on a particular Pack.")
    partner_id = fields.Many2one(
        'res.partner', 'Inventoried Owner',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="Specify Owner to focus your inventory on a particular Owner.")
    lot_id = fields.Many2one(
        'stock.production.lot', 'Inventoried Lot/Serial Number',
        copy=False, readonly=True,
        states={'draft': [('readonly', False)]},
        help="Specify Lot/Serial Number to focus your inventory on a particular Lot/Serial Number.")
    filter = fields.Selection(
        string='盘点', selection='_selection_filter',
        required=True,
        default='none',
        help="If you do an entire inventory, you can choose 'All Products' and it will prefill the inventory with the current stock.  If you only do some products  "
             "(e.g. Cycle Counting) you can choose 'Manual Selection of Products' and the system won't propose anything.  You can also let the "
             "system propose for a single product / lot /... ")
    total_qty = fields.Float(u'数量总计', compute='_compute_total_qty')
    category_id = fields.Many2one(
        'product.category', 'Inventoried Category',
        readonly=True, states={'draft': [('readonly', False)]},
        help="Specify Product Category to focus your inventory on a particular Category.")
    exhausted = fields.Boolean(u'包含短缺的产品', readonly=True, states={'draft': [('readonly', False)]})

    @api.one
    def _compute_total_qty(self):
        self.total_qty = sum(self.mapped('line_ids').mapped('product_qty'))

    @api.model
    def _selection_filter(self):
        """ Get the list of filter allowed according to the options checked
        in 'Settings\Warehouse'. """
        res_filter = [
            ('none', _('All products')),
            ('category', _('One product category')),
            ('product', _('One product only')),
            ('partial', _('Select products manually'))]

        if self.user_has_groups('stock.group_tracking_owner'):
            res_filter += [('owner', _('One owner only')), ('product_owner', _('One product for a specific owner'))]
        if self.user_has_groups('stock.group_production_lot'):
            res_filter.append(('lot', _('One Lot/Serial Number')))
        if self.user_has_groups('stock.group_tracking_lot'):
            res_filter.append(('pack', _('A Pack')))
        return res_filter

    @api.onchange('filter')
    def onchange_filter(self):
        if self.filter not in ('product', 'product_owner'):
            self.product_id = False
        if self.filter != 'lot':
            self.lot_id = False
        if self.filter not in ('owner', 'product_owner'):
            self.partner_id = False
        if self.filter != 'pack':
            self.package_id = False
        if self.filter != 'category':
            self.category_id = False
        if self.filter == 'product':
            self.exhausted = True

    @api.one
    @api.constrains('filter', 'product_id', 'lot_id', 'partner_id', 'package_id')
    def _check_filter_product(self):
        if self.filter == 'none' and self.product_id and self.location_id and self.lot_id:
            return
        if self.filter not in ('product', 'product_owner') and self.product_id:
            raise UserError(_('The selected inventory options are not coherent.'))
        if self.filter != 'lot' and self.lot_id:
            raise UserError(_('The selected inventory options are not coherent.'))
        if self.filter not in ('owner', 'product_owner') and self.partner_id:
            raise UserError(_('The selected inventory options are not coherent.'))
        if self.filter != 'pack' and self.package_id:
            raise UserError(_('The selected inventory options are not coherent.'))

    @api.multi
    def action_reset_product_qty(self):
        self.mapped('line_ids').write({'product_qty': 0})
        return True
    reset_real_qty = action_reset_product_qty

    @api.multi
    def action_done(self):
        negative = next((line for line in self.mapped('line_ids') if line.product_qty < 0 and line.product_qty != line.theoretical_qty), False)
        if negative:
            raise UserError(_('You cannot set a negative product quantity in an inventory line:\n\t%s - qty: %s') % (negative.product_id.name, negative.product_qty))
        self.action_check()
        self.write({'state': 'done'})
        self.post_inventory()
        return True

    @api.multi
    def post_inventory(self):
        # The inventory is posted as a single step which means quants cannot be moved from an internal location to another using an inventory
        # as they will be moved to inventory loss, and other quants will be created to the encoded quant location. This is a normal behavior
        # as quants cannot be reuse from inventory location (users can still manually move the products before/after the inventory if they want).
        self.mapped('move_ids').filtered(lambda move: move.state != 'done').action_done()

    @api.multi
    def action_check(self):
        """ Checks the inventory and computes the stock move to do """
        # tde todo: clean after _generate_moves
        for inventory in self:
            # first remove the existing stock moves linked to this inventory
            inventory.mapped('move_ids').unlink()
            for line in inventory.line_ids:
                # compare the checked quantities on inventory lines to the theorical one
                stock_move = line._generate_moves()

    @api.multi
    def action_cancel_draft(self):
        for line in self.line_ids:
            if line.state!='done':
                objs=self.env['product.detail.account'].search([('product_id','=',line.product_id.id)])
                objs2=self.env['inventory.cost'].search([('product_id','=',line.product_id.id)])
                for obj in objs:
                    obj.unlink()
                for obj in objs2:
                    obj.unlink()

        self.mapped('move_ids').action_cancel()
        self.write({
            'line_ids': [(5,)],
            'state': 'draft'
        })


    @api.multi
    def action_start(self):
        for inventory in self:
            vals = {'state': 'confirm', 'date': fields.Datetime.now()}
            if (inventory.filter != 'partial') and not inventory.line_ids:
                vals.update({'line_ids': [(0, 0, line_values) for line_values in inventory._get_inventory_lines_values()]})
            inventory.write(vals)
        return True
    prepare_inventory = action_start

    @api.multi
    def _get_inventory_lines_values(self):
        # TDE CLEANME: is sql really necessary ? I don't think so
        locations = self.env['stock.location'].search([('id', 'child_of', [self.location_id.id])])
        domain = ' location_id in %s'
        args = (tuple(locations.ids),)

        vals = []
        Product = self.env['product.product']
        # Empty recordset of products available in stock_quants
        quant_products = self.env['product.product']
        # Empty recordset of products to filter
        products_to_filter = self.env['product.product']

        #case 1: Filter on One owner only or One product for a specific owner
        if self.partner_id:
            domain += ' AND owner_id = %s'
            args += (self.partner_id.id,)
        #case 2: Filter on One Lot/Serial Number
        if self.lot_id:
            domain += ' AND lot_id = %s'
            args += (self.lot_id.id,)
        #case 3: Filter on One product
        if self.product_id:
            domain += ' AND product_id = %s'
            args += (self.product_id.id,)
            products_to_filter |= self.product_id
        #case 4: Filter on A Pack
        if self.package_id:
            domain += ' AND package_id = %s'
            args += (self.package_id.id,)
        #case 5: Filter on One product category + Exahausted Products
        if self.category_id:
            categ_products = Product.search([('categ_id', '=', self.category_id.id)])
            domain += ' AND product_id = ANY (%s)'
            args += (categ_products.ids,)
            products_to_filter |= categ_products

        self.env.cr.execute("""SELECT product_id, sum(qty) as product_qty, location_id, lot_id as prod_lot_id, package_id, owner_id as partner_id
            FROM stock_quant
            WHERE %s
            GROUP BY product_id, location_id, lot_id, package_id, partner_id """ %domain, args)

        for product_data in self.env.cr.dictfetchall():
            # replace the None the dictionary by False, because falsy values are tested later on
            for void_field in [item[0] for item in product_data.items() if item[1] is None]:
                product_data[void_field] = False
            product_data['theoretical_qty'] = product_data['product_qty']
            if product_data['product_id']:
                product_data['product_uom_id'] = Product.browse(product_data['product_id']).uom_id.id
                quant_products |= Product.browse(product_data['product_id'])
            vals.append(product_data)
        if self.exhausted:
            exhausted_vals = self._get_exhausted_inventory_line(products_to_filter, quant_products)
            vals.extend(exhausted_vals)
        return vals

    def _get_exhausted_inventory_line(self, products, quant_products):
        '''
        This function return inventory lines for exausted products
        :param products: products With Selected Filter.
        :param quant_products: products available in stock_quants
        '''
        vals = []
        exhausted_domain = [('type', 'not in', ('service', 'consu', 'digital'))]
        if products:
            exhausted_products = products - quant_products
            exhausted_domain += [('id', 'in', exhausted_products.ids)]
        else:
            exhausted_domain += [('id', 'not in', quant_products.ids)]
        exhausted_products = self.env['product.product'].search(exhausted_domain)
        for product in exhausted_products:
            vals.append({
                'inventory_id': self.id,
                'product_id': product.id,
                'location_id': self.location_id.id,
            })
        return vals

class data_fill_line(models.Model):
    _name='data.fill.line'
    _order = "product_name ,inventory_id, location_name, product_code, prodlot_name"

    inventory_id = fields.Many2one(
        'data.fill', '序列号名称',
        index=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', '所有者')
    product_id = fields.Many2one(
        'product.product', '产品',
        index=True, required=True)
    product_name = fields.Char(
        u'产品名称', related='product_id.name', store=True)
    product_code = fields.Char(
        u'产品代码', related='product_id.default_code', store=True)
    product_uom_id = fields.Many2one(
        'product.uom', '产品计量单位',
        required=True,
        default=lambda self: self.env.ref('product.product_uom_unit', raise_if_not_found=True))
    product_qty = fields.Float(
        u'点检的数量',
        digits=dp.get_precision('Product Unit of Measure'), default=0)
    location_id = fields.Many2one(
        'stock.location', '地点',
        index=True, required=True)
    # TDE FIXME: necessary ? only in order -> replace by location_id
    location_name = fields.Char(
        u'位置名称', related='location_id.complete_name', store=True)
    package_id = fields.Many2one(
        'stock.quant.package', '打包', index=True)
    prod_lot_id = fields.Many2one(
        'stock.production.lot', '批次/序列号',
        domain="[('product_id','=',product_id)]")
    # TDE FIXME: necessary ? -> replace by location_id
    prodlot_name = fields.Char(
        u'序列号名称',
        related='prod_lot_id.name', store=True)
    company_id = fields.Many2one(
        'res.company', '公司', related='inventory_id.company_id',
        index=True, readonly=True, store=True)
    # TDE FIXME: necessary ? -> replace by location_id
    state = fields.Selection(
        u'状态',  related='inventory_id.state', readonly=True)
    theoretical_qty = fields.Float(
        u'理论数量', compute='_compute_theoretical_qty',
        digits=dp.get_precision('Product Unit of Measure'), readonly=True, store=True)
    unit_price=fields.Float(u'单价')
    total_price=fields.Float(u'总价')
#-----------mlp
    @api.onchange('product_qty','unit_price')
    def sum_total(self):
        self.total_price=self.product_qty*self.unit_price


    @api.one
    @api.depends('location_id', 'product_id', 'package_id', 'product_uom_id', 'company_id', 'prod_lot_id', 'partner_id')
    def _compute_theoretical_qty(self):
        if not self.product_id:
            self.theoretical_qty = 0
            return
        theoretical_qty = sum([x.qty for x in self._get_quants()])
        if theoretical_qty and self.product_uom_id and self.product_id.uom_id != self.product_uom_id:
            theoretical_qty = self.product_id.uom_id._compute_quantity(theoretical_qty, self.product_uom_id)
        self.theoretical_qty = theoretical_qty

    @api.onchange('product_id', 'product_uom_id')
    def onchange_product_or_uom(self):
        res = {}
        # If no UoM or incorrect UoM put default one from product
        if self.product_id and (not self.product_uom_id or self.product_id.uom_id.category_id != self.product_uom_id.category_id):
            self.product_uom_id = self.product_id.uom_id
            res['domain'] = {'product_uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        return res

    @api.onchange('product_id', 'location_id', 'product_uom_id', 'prod_lot_id', 'partner_id', 'package_id')
    def onchange_quantity_context(self):
        if self.product_id and self.location_id and self.product_id.uom_id.category_id == self.product_uom_id.category_id:  # TDE FIXME: last part added because crash
            self._compute_theoretical_qty()
            self.product_qty = self.theoretical_qty

    @api.model
    def create(self, values):
        if 'product_id' in values and 'product_uom_id' not in values:
            values['product_uom_id'] = self.env['product.product'].browse(values['product_id']).uom_id.id
        existings = self.search([
            ('product_id', '=', values.get('product_id')),
            ('inventory_id.state', '=', 'confirm'),
            ('location_id', '=', values.get('location_id')),
            ('partner_id', '=', values.get('partner_id')),
            ('package_id', '=', values.get('package_id')),
            ('prod_lot_id', '=', values.get('prod_lot_id'))])
        res = super(data_fill_line, self).create(values)
        if existings:
            raise UserError(_("You cannot have two inventory adjustements in state 'in Progess' with the same product"
                              "(%s), same location(%s), same package, same owner and same lot. Please first validate"
                              "the first inventory adjustement with this product before creating another one.") % (res.product_id.name, res.location_id.name))
        #--------------mlp
        self.env['product.detail.account'].create({
            'balance_qty':res.product_qty,
            'balance_price':res.unit_price,
            'balance_amount':res.total_price,
            'change_date':res.inventory_id.date,
            'product_id':res.product_id.id
        })
        self.env['inventory.cost'].create({
            'stock':res.product_qty,
            'current_cost':res.unit_price,
            'current_amount':res.total_price,
            'change_date':res.inventory_id.date,
            'product_id':res.product_id.id
        })
        return res

    def _get_quants(self):
        return self.env['stock.quant'].search([
            ('company_id', '=', self.company_id.id),
            ('location_id', '=', self.location_id.id),
            ('lot_id', '=', self.prod_lot_id.id),
            ('product_id', '=', self.product_id.id),
            ('owner_id', '=', self.partner_id.id),
            ('package_id', '=', self.package_id.id)])

    def _generate_moves(self):
        moves = self.env['stock.move']
        Quant = self.env['stock.quant']
        for line in self:
            if float_utils.float_compare(line.theoretical_qty, line.product_qty, precision_rounding=line.product_id.uom_id.rounding) == 0:
                continue
            diff = line.theoretical_qty - line.product_qty
            vals = {
                'name': _('INV:') + (line.inventory_id.name or ''),
                'product_id': line.product_id.id,
                'product_uom': line.product_uom_id.id,
                'date': line.inventory_id.date,
                'company_id': line.inventory_id.company_id.id,
                'inventory_id': line.inventory_id.id,
                'state': 'confirmed',
                'restrict_lot_id': line.prod_lot_id.id,
                'restrict_partner_id': line.partner_id.id}
            if diff < 0:  # found more than expected
                vals['location_id'] = line.product_id.property_stock_inventory.id
                vals['location_dest_id'] = line.location_id.id
                vals['product_uom_qty'] = abs(diff)
            else:
                vals['location_id'] = line.location_id.id
                vals['location_dest_id'] = line.product_id.property_stock_inventory.id
                vals['product_uom_qty'] = diff
            move = moves.create(vals)

            if diff > 0:
                domain = [('qty', '>', 0.0), ('package_id', '=', line.package_id.id), ('lot_id', '=', line.prod_lot_id.id), ('location_id', '=', line.location_id.id)]
                preferred_domain_list = [[('reservation_id', '=', False)], [('reservation_id.inventory_id', '!=', line.inventory_id.id)]]
                quants = Quant.quants_get_preferred_domain(move.product_qty, move, domain=domain, preferred_domain_list=preferred_domain_list)
                Quant.quants_reserve(quants, move)
            elif line.package_id:
                move.action_done()
                move.quant_ids.write({'package_id': line.package_id.id})
                quants = Quant.search([('qty', '<', 0.0), ('product_id', '=', move.product_id.id),
                                       ('location_id', '=', move.location_dest_id.id), ('package_id', '!=', False)], limit=1)
                if quants:
                    for quant in move.quant_ids:
                        if quant.location_id.id == move.location_dest_id.id:  #To avoid we take a quant that was reconcile already
                            quant._quant_reconcile_negative(move)
        return moves
