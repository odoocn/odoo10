# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DSaleOrderLine(models.Model):
    _name = 'sale.order.line'
    _inherit = 'sale.order.line'

    isbn = fields.Char(string=u'ISBN')
    box_ids = fields.One2many('ecps.box', 'order_line_id', string=u'箱号')
    barcode = fields.Char(related='product_id.barcode', string=u'条码')
    item_id = fields.Many2one('ecps.items', string=u'商品')
    # remark = fields.Text(string=u'备注')
    originalNum = fields.Float(string=u'原始数量')
    actualNum = fields.Float(string=u'实收数量')
    state = fields.Selection([
        ('draft', '新单'),
        ('sent', '已发送至仓库'),
        ('sale', '销售订单'),
        ('done', '完成'),
        ('cancel', '取消'),
    ], related='order_id.state', string='订单状态', readonly=True, copy=False, store=True, default='draft')

    @api.model
    def create(self, values):
        if (not values.get('originalNum')) or values['originalNum'] == 0:
            values['originalNum'] = values['product_uom_qty']
        return super(DSaleOrderLine, self).create(values)


class DSaleOrder(models.Model):
    _name = "sale.order"
    _inherit = 'sale.order'
    _order = 'order_start_time desc,location_mark,location_province,location_city,location_district'

    vendor_name = fields.Char(string=u'供应商名称')
    vendor_code = fields.Char(string=u'供应商编号')

    pur_erp = fields.Char(string=u'采购员')

    location_province = fields.Many2one('res.province', string=u'省')
    location_city = fields.Many2one('res.city', string=u'市')
    location_district = fields.Many2one('res.district', string=u'县')
    location_details = fields.Char(u'详细地址')
    location_mark = fields.Char(u'大头笔')

    deliverCenterId = fields.Integer(string=u'配送中心ID')
    deliverCenterName = fields.Char(string=u'配送中心名称')
    warehouseName = fields.Char(string=u'仓库')

    delivery_phone = fields.Char(u'收件人电话')
    delivery_name = fields.Char(u'收件人姓名')
    invoice_info = fields.Char(u'开票信息')

    express_com = fields.Many2one('ecps.express', string=u'快递公司')
    express_code = fields.Char(u'快递单号', readonly=True)
    express_paytype = fields.Selection([('1', '现付'), ('2', '到付'), ('3', '月结'), ('4', '第三方支付')], string=u'支付方式',
                                       readonly=True)

    source_shop = fields.Many2one('ecps.shop', string=u'来源店铺')
    source_code = fields.Char(string=u'来源单号')

    back_boolean = fields.Boolean(string=u'是否退货', default=False, readonly=True)
    delivery_boolean = fields.Boolean(string=u'是否已发货', default=False, readonly=True)
    error_boolean = fields.Boolean(string=u'异常订单', default=False, readonly=True)
    combine_state = fields.Selection([('becombined', '被合单'), ('uncombined', '未合单'), ('child', '合单')],
                                     default='uncombined', string=u'合单状态')
    order_state = fields.Char(string=u'订单状态')
    order_start_time = fields.Datetime(string=u'下单时间')
    order_end_time = fields.Datetime(string=u'订单完成时间')

    order_step = fields.Selection([(-1, '已取消'), (0, '新单'), (1, '可确认'), (2, '可完成'), (3, '已完成')], default=0,
                                  string=u'相对状态')

    confirm_need = fields.Boolean(string=u'需要回告', default=False)
    return_state = fields.Boolean(string=u'回告完成', default=False)
    return_create = fields.Boolean(string=u'回告已生成', default=False)

    combine_orders = fields.Many2one('sale.order', string=u'合单于', readonly=True)
    history_orders = fields.One2many('sale.order', 'combine_orders', string=u'历史订单', readonly=True)

    direct_group = fields.Selection([('2B', 'To B'), ('2C', 'To C')], string=u'面向对象', compute='compute_groups',
                                    store=True)

    online_type = fields.Selection([('online', '线上'), ('offline', '线下')], string=u'订单来源', default='offline', required=True)
    syn_type = fields.Boolean(string=u'同步线上信息', default=False, required=True)
    special_order = fields.Char(string=u'特殊单据')

    weight_total = fields.Float(string=u'总重')

    state = fields.Selection([
        ('draft', u'新单'),
        ('sent', u'送出'),
        ('checking', u'审核中'),
        ('reject', u'驳回'),
        ('sale', u'销售订单'),
        ('done', u'完成'),
        ('cancel', u'已取消'),
    ], string='状态', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    @api.onchange('source_shop')
    def set_warehouse_from_shop(self):
        self.warehouse_id = self.source_shop.default_warehouse.id

    @api.multi
    def syn_orders(self, shop_id=False):
        result = {'code': 0, 'result': []}
        if shop_id:
            shop = self.env['ecps.shop'].browse(shop_id)
            if not shop.access_token:
                return {'code': -1, 'result': "店铺 %s 未授权" % self.source_shop.name}
            for order in self.env['sale.order'].search(
                    [('syn_type', '=', True), ('state', 'not in', ('done', 'cancel')),
                     ('source_shop', '=', shop_id)]):
                res = order.syn_order()
                if not res['code'] == 0:
                    result['code'] = -1
                    result['result'].append(res)
        else:
            for shop in self.env['ecps.shop'].search([]):
                if not shop.access_token:
                    result['code'] = -1
                    result['result'].append({'code': -1, 'result': "店铺 %s 未授权" % self.source_shop.name})
                else:
                    for order in self.env['sale.order'].search(
                            [('syn_type', '=', True), ('state', 'not in', ('done', 'cancel')),
                             ('source_shop', '=', shop.id)]):
                        res = order.syn_order()
                        if not res['code'] == 0:
                            result['code'] = -1
                            result['result'].append(res)
        return result

    @api.multi
    def syn_order(self):
        link_api = self.source_shop.plate_id.get_api(access_token=self.source_shop.access_token.encode('utf-8'))[0]
        result = link_api.sychronize_orders(order_ids=[self.source_code.encode('utf-8')],
                                            shop_type=self.source_shop.shop_type.encode('utf-8'))
        if result['code'] == 0:
            for res in result['result']:
                self.write({'location_province': self.env['res.province'].get_province(res['location_province']),
                            'location_city': self.env['res.city'].get_city(res['location_city']),
                            'location_district': self.env['res.district'].get_district(res['location_district']),
                            'location_details': res['location_details'],
                            'location_mark': res['location_mark'],
                            'order_state': res['order_state'],
                            'delivery_name': res['delivery_name'],
                            'delivery_phone': res['delivery_phone'],
                            'deliverCenterId': res['deliverCenterId'],
                            'deliverCenterName': res['deliverCenterName'],
                            'confirm_need': res['confirm_need'],
                            'return_state': not res['confirm_need'],
                            'order_start_time': res['order_start_time'],
                            'order_end_time': res['order_end_time'],
                            'pur_erp': res['pur_erp'],
                            'warehouseName': res.get('warehouseName', False),
                            'error_boolean': False,
                            'invoice_info': res.get('invoice_info'),
                            'special_order': res.get('special_order')})
                for line in res['details']:
                    item = self.env['ecps.items'].search([('item_sku', '=', line['sku_id']),
                                                          ('shop_id', '=', self.source_shop.id)])
                    if len(item) > 1:
                        self.write({'error_boolean': True})
                        return {'code': -1, 'result': _("店铺 %s 下，sku为 %s 的商品存在多个。请处理。") %
                                                      (self.source_shop.name, line['sku_id'])}
                    if len(item) == 0:
                        self.write({'error_boolean': True})
                        return {'code': -1, 'result': _("店铺 %s 下，sku为 %s 的商品不存在。请处理。") %
                                                      (self.source_shop.name, line['sku_id'])}
                    product = item.product_id
                    if not product:
                        self.write({'error_boolean': True})
                        return {'code': -1,
                                'result': _("%s 店铺下 %s (%s)的商品还未匹配") % (self.name, item.name, line['sku_id'])}
                    order_line = self.env['sale.order.line'].search(
                        [('order_id', '=', self.id), ('item_id', '=', item.id)])
                    if order_line:
                        order_line[0].write(
                            {'name': line['remark'] if line.get('remark') else product.product_tmpl_id.name,
                             'product_id': product.id,
                             'state': 'draft',
                             'item_id': item.id,
                             'tax_id': [],
                             'price_unit': line['price'],
                             'product_uom_qty': line['num'],
                             'actualNum': line['actualNum'],
                             'originalNum': line['originalNum'],
                             'product_uom': product.product_tmpl_id.uom_id.id})
                    else:
                        self.env['sale.order.line'].create({'order_id': self.id,
                                                            'name': line['remark'] if line.get(
                                                                'remark') else product.product_tmpl_id.name,
                                                            'product_id': product.id,
                                                            'customer_lead': product.product_tmpl_id.sale_delay,
                                                            'discount': 0,
                                                            # 'invoice_status': 'no',
                                                            'procurement_ids': [],
                                                            'qty_delivered_updateable': True,
                                                            'route_id': False,
                                                            # 'state': 'draft',
                                                            'item_id': item.id,
                                                            'tax_id': [],
                                                            'price_unit': line['price'],
                                                            'product_uom_qty': line['num'],
                                                            'actualNum': line['actualNum'],
                                                            'originalNum': line['originalNum'],
                                                            'product_uom': product.product_tmpl_id.uom_id.id})
        else:
            return result
        if result['result'][0]['order_step'] < 0 or result['result'][0]['delete_mark']:
            self.action_cancel()
            self.write({'order_step': -1})
        elif result['result'][0]['order_step'] > self.order_step:
            if result['result'][0]['order_step'] == 0:
                self.action_draft()
            if result['result'][0]['order_step'] >= 1:
                self.action_confirm()
                self.write({'order_step': 1})
            if result['result'][0]['order_step'] == 2:
                self.action_done()
                # track = self.env['order.track'].create({
                #             'name': self.name + '-' + self.source_shop.name or '/' + '-' + self.source_code or '/' + '-',
                #             'type': 'sale',
                #             'sale_id': self.id,
                #         })
                # for line in self.order_line:
                #     self.env['order.track.line'].create({
                #         'product_id': line.product_id.id,
                #         'item_id': line.item_id.id,
                #         'originNum': line.originalNum,
                #         'actualNum': line.actualNum,
                #         'confirmNum': line.product_uom_qty,
                #     })
                self.write({'order_step': 3})
        self.env.cr.commit()
        return {'code': 0}

    @api.multi
    def action_done(self):
        self.write({'state': 'done'})
        for r in self:
            if r.online_type == 'online':
                track = self.env['order.track'].create({
                    'name': r.name + '-' + r.source_shop.name or '/' + '-' + r.source_code or '/' + '-',
                    'type': 'sale',
                    'sale_id': r.id,
                })
                for line in r.order_line:
                    self.env['order.track.line'].create({
                        'product_id': line.product_id.id,
                        'item_id': line.item_id.id,
                        'originNum': line.originalNum,
                        'actualNum': line.actualNum,
                        'confirmNum': line.product_uom_qty,
                        'track_id': track.id
                    })
        return True

    @api.depends('source_shop')
    def compute_groups(self):
        for r in self:
            r.direct_group = r.source_shop.direct_group

    @api.multi
    def action_quotation_send(self):
        self.ensure_one()
        self.write({'state': 'sent'})

    @api.multi
    def action_return_view(self):
        self.ensure_one()
        qty_id = self.env['qty.confirm'].search({'order_id', '=', self.id})
        if not qty_id:
            raise UserError(_("%s 订单未生成回告") % self.name)
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('driserp.qty_confirm_action')
        list_view_id = imd.xmlid_to_res_id('driserp.qty_confirm_tree_view')
        form_view_id = imd.xmlid_to_res_id('driserp.qty_confirm_form_view')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form']],
            'target': 'current',
            'context': action.context,
            'res_model': action.res_model,
            'res_id': qty_id[0].id,
        }
        return result

    @api.multi
    def action_return_create(self):
        self.ensure_one()
        qty_id = self.env['qty.confirm'].create({'order_id': self.id, 'name': self.name + u'回告'})
        for line in self.order_line:
            self.env['qty.confirm.line'].create({
                'confirm_id': qty_id.id,
                'item_id': line.item_id.id,
                'product_id': line.product_id.id,
                'originalNum': line.originalNum,
                'confirmedNum': line.originalNum,
                'deliverCenterId': line.deliverCenterId,
                'deliverCenterName': line.deliverCenterName,
            })
        self.write({'return_create': True})
        return self.action_return_view()

    @api.multi
    def combine_order(self):
        # 合单操作
        if len(self.env.context['records']) == 0:
            return True
        ids = str(tuple(self.env.context['records']))
        # for r in self:
        #     ids.append(r.id)
        # ids = str(tuple(ids)).replace(' ', '')
        self.env.cr.execute("""
    SELECT count(s.id) as length,
location_province,
location_city,
location_district,
location_details,
delivery_phone,
delivery_name
    FROM sale_order s
    WHERE s.id in %s
    GROUP BY location_province,location_city,location_district,location_details,delivery_phone,delivery_name
    HAVING count(s.id) > 1;
        """ % ids)
        res = self.env.cr.dictfetchall()
        if len(res) > 0:
            res_lines = []
            for r in res:
                res_obj = self.search([('id', 'in', self.env.context['records']),
                                       ('location_province', '=', r['location_province']),
                                       ('location_city', '=', r['location_city']),
                                       ('location_district', '=', r['location_district']),
                                       ('location_details', '=', r['location_details']),
                                       ('delivery_phone', '=', r['delivery_phone']),
                                       ('delivery_name', '=', r['delivery_name'])])
                new_order = res_obj[0].copy()
                new_order.write({'combine_state': 'child'})
                new_order.order_line.unlink()
                new_lines = []
                products_line = {}
                for res_o in res_obj:
                    for line in res_o.order_line:
                        if str(line.product_id.id) in products_line.keys():
                            old_line = self.env['sale.order.line'].browse(products_line[str(line.product_id.id)])
                            old_line.write({'product_uom_qty': old_line.product_uom_qty + line.product_uom_qty})
                        else:
                            new_line = self.env['sale.order.line'].create({'order_id': new_order.id,
                                                                           'name': line.name,
                                                                           'sequence': line.sequence,
                                                                           'invoice_status': line.invoice_status,
                                                                           'price_unit': line.price_unit,
                                                                           'price_subtotal': line.price_subtotal,
                                                                           'price_tax': line.price_tax,
                                                                           'price_total': line.price_total,
                                                                           'price_reduce': line.price_reduce,
                                                                           'tax_id': line.tax_id,
                                                                           'discount': line.discount,
                                                                           'product_id': line.product_id.id,
                                                                           'product_uom_qty': line.product_uom_qty,
                                                                           'product_uom': line.product_uom.id,
                                                                           'qty_delivered_updateable': line.qty_delivered_updateable,
                                                                           'qty_delivered': line.qty_delivered,
                                                                           'qty_to_invoice': line.qty_to_invoice,
                                                                           'qty_invoiced': line.qty_invoiced,
                                                                           'order_partner_id': line.order_partner_id.id,
                                                                           'state': line.state,
                                                                           'customer_lead': line.customer_lead,
                                                                           'sku_item': line.sku_item.id})
                            new_lines.append(new_line.id)
                            products_line[str(line.product_id.id)] = new_line.id
                res_obj.write({'combine_state': 'becombined', 'combine_orders': new_order.id})
                # res_obj.action_cancel()
        return True

    @api.multi
    def action_confirm(self):
        for order in self:
            order.state = 'sale'
            if self.env.context.get('send_email'):
                self.force_quotation_send()
            if order.source_shop.shop_type == 'fbp':
                for line in order.order_line:
                    move = self.env['stock.move'].create({'product_id': line.product_id.id,
                                                          'product_uom_qty': line.product_uom_qty,
                                                          'product_uom': line.product_uom.id,
                                                          'origin': order.name,
                                                          'location_id': order.source_shop.fbp_loc.id,
                                                          'location_dest_id': self.env['stock.location'].search(
                                                              {'usage', '=', 'customer'})[0].id,
                                                          'partner_id': order.partner_id.id})
                    move.force_assign()
                    move.action_confirm()
            else:
                order.order_line._action_procurement_create()
            if not order.project_id:
                for line in order.order_line:
                    if line.product_id.invoice_policy == 'cost':
                        order._create_analytic_account()
                        break
        if self.env['ir.values'].get_default('sale.config.settings', 'auto_done_setting'):
            self.action_done()
        return True
