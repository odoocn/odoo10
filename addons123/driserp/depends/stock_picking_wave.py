# -*- coding: utf-8 -*-
from odoo import api, models, fields
from odoo.tools.translate import _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp
from cStringIO import StringIO

try:
    import xlwt
except ImportError:
    xlwt = None


class DStockPickingWaveLine(models.Model):
    _name = 'stock.picking.wave.line'

    product_id = fields.Many2one('product.product', '产品', required=True, select=True,
                                 domain=[('type', 'in', ['product', 'consu'])])
    product_uom_qty = fields.Float(string='数量', digits=dp.get_precision('Product Unit of Measure'), required=True,
                                   default=1.0)
    product_uom = fields.Many2one('product.uom', string='单位', required=True)
    product_done = fields.Float('已完成', default=0)
    picking_wave_id = fields.Many2one('stock.picking.wave', string=u'波次')


class MarkPickingWave(models.Model):
    _name = 'stock.picking.wave.mark'

    _order = 'name,product_id'

    name = fields.Char(string=u'大头笔')
    product_id = fields.Many2one('product.product', '产品', required=True, select=True,
                                 domain=[('type', 'in', ['product', 'consu'])])
    product_uom_qty = fields.Float(string='数量', digits=dp.get_precision('Product Unit of Measure'), required=True,
                                   default=1.0)
    product_uom = fields.Many2one('product.uom', string='单位', required=True)
    product_done = fields.Float('已完成', default=0)
    picking_wave_id = fields.Many2one('stock.picking.wave', string=u'波次')


class DStockPickingWave(models.Model):
    _name = "stock.picking.wave"
    _inherit = 'stock.picking.wave'

    product_line = fields.One2many('stock.picking.wave.line', 'picking_wave_id', string=u'产品',
                                   compute='compute_line', store=True)
    mark_line = fields.One2many('stock.picking.wave.mark', 'picking_wave_id', string=u'大头笔',
                                compute='compute_line', store=True)
    direct_group = fields.Selection([('2B', 'To B'), ('2C', 'To C')], string=u'面向人群',
                                    help=u"添加出货单时需要选择面向人群，内部调拨则置空")
    empty = fields.Boolean(default=True)

    @api.depends('picking_ids')
    def is_empty(self):
        if self.picking_ids:
            self.empty = False

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('picking.wave') or '/'
        res = super(DStockPickingWave, self).create(vals)
        for picking in res.picking_ids:
            if not picking.direct_group == res.direct_group:
                raise UserError(_("拣货单 %s 与波次 %s 面向人群不同！") % (picking.name, r.name))
        res.compute_product_line()
        return res

    # def confirm_picking(self, cr, uid, ids, context=None):
    #     picking_todo = self.pool.get('stock.picking').search(cr, uid, [('wave_id', 'in', ids),
    #                                                                    ('state', 'not in', ('done', 'cancel'))],
    #                                                          context=context)
    #     self.write(cr, uid, ids, {'state': 'in_progress'}, context=context)
    #     return self.pool.get('stock.picking').action_assign(cr, uid, picking_todo, context=context)

    @api.multi
    def write(self, values):
        values['product_line'] = [[6, False, []]]
        values['mark_line'] = [[6, False, []]]
        r = super(DStockPickingWave, self).write(values)
        for t in self:
            for picking in t.picking_ids:
                if not picking.direct_group == t.direct_group:
                    raise UserError(_("拣货单 %s 与波次 %s 面向人群不同！") % (picking.name, t.name))
            t.compute_product_line()
        return r

    @api.multi
    def box_create(self):
        for wave in self:
            for picking in wave.picking_ids:
                result = []
                box_amount = 0
                order = picking.sale_id
                for line in order.order_line:
                    qty = line.product_uom_qty
                    oq = qty
                    while qty > 0:
                        box_amount += 1
                        result.append({'wave_id': wave.id,
                                       'picking_id': picking.id,
                                       'order_line_id': line.id,
                                       'to_place': order.partner_id.name + " "
                                                   + order.deliverCenterName,
                                       'address': order.location_details,
                                       'contact_name': order.delivery_name,
                                       'contact_phone': order.delivery_phone,
                                       'order_code': order.source_code,
                                       'item_id': line.item_id.name,
                                       'barcode': line.item_id.code,
                                       'box_no': box_amount,
                                       'origin_num': oq,
                                       'inner_num': line.product_id.uom_stock_id.factor_inv if qty > line.product_id.uom_stock_id.factor_inv else qty,
                                       'name': order.source_shop.name + u" 发货铁箱单 " + str(box_amount)
                                       })
                        if line.product_id.uom_stock_id:
                            qty -= line.product_id.uom_stock_id.factor_inv
                        else:
                            qty -= 1
                for r in result:
                    r['box_num'] = box_amount
                    self.env['ecps.box'].create(r)
        return True

    @api.multi
    def done(self):
        pickings = self.mapped('picking_ids').filtered(lambda picking: picking.state not in ('cancel', 'done'))
        if any(picking.state != 'assigned' for picking in pickings):
            raise UserError(_(
                'Some pickings are still waiting for goods. Please check or force their availability before setting this wave to done.'))
        for picking in pickings:
            picking.message_post(
                body="<b>%s:</b> %s <a href=#id=%s&view_type=form&model=stock.picking.wave>%s</a>" % (
                    _("Transferred by"),
                    _("Picking Wave"),
                    picking.wave_id.id,
                    picking.wave_id.name))
        if pickings:
            pickings.with_context(picking_done=True).do_new_transfer()
        self.box_create()
        return self.write({'state': 'done'})

    @api.one
    def compute_product_line(self):
        for line in self.product_line:
            line.unlink()
        for line in self.mark_line:
            line.unlink()
        product_line = {}
        mark_line = {}
        for picking in self.picking_ids:
            for move in picking.move_lines:
                if picking.destination_mark in mark_line.keys():
                    if move.product_id.id in mark_line[picking.destination_mark].keys():
                        pro = self.env['stock.picking.wave.mark'].browse(
                            mark_line[picking.destination_mark][move.product_id.id])
                        pro.write({'product_uom_qty': pro.product_uom_qty + move.product_uom_qty})
                    else:
                        new_line = self.env['stock.picking.wave.mark'].create({'product_id': move.product_id.id,
                                                                               'product_uom_qty': move.product_uom_qty,
                                                                               'product_uom': move.product_uom.id,
                                                                               'picking_wave_id': self.id,
                                                                               'name': picking.destination_mark})
                        mark_line[picking.destination_mark][move.product_id.id] = new_line.id
                else:
                    new_line = self.env['stock.picking.wave.mark'].create({'product_id': move.product_id.id,
                                                                           'product_uom_qty': move.product_uom_qty,
                                                                           'product_uom': move.product_uom.id,
                                                                           'picking_wave_id': self.id,
                                                                           'name': picking.destination_mark})
                    mark_line[picking.destination_mark] = {move.product_id.id: new_line.id}

                if move.product_id.id in product_line.keys():
                    pro = self.env['stock.picking.wave.line'].browse(product_line[move.product_id.id])
                    pro.write({'product_uom_qty': pro.product_uom_qty + move.product_uom_qty})
                else:
                    new_line = self.env['stock.picking.wave.line'].create({'product_id': move.product_id.id,
                                                                           'product_uom_qty': move.product_uom_qty,
                                                                           'product_uom': move.product_uom.id,
                                                                           'picking_wave_id': self.id})
                    product_line[move.product_id.id] = new_line.id
        return True

    @api.multi
    def print_product(self):
        if not self.ids:
            raise UserError(_('Nothing to print.'))
        return self.env["report"].with_context(active_ids=self.ids, active_model='stock.picking.wave').\
            get_action([], 'driserp.report_product')

    @api.multi
    def print_product_mark(self):
        if not self.ids:
            raise UserError(_('Nothing to print.'))
        return self.env["report"].with_context(active_ids=self.ids, active_model='stock.picking.wave').\
            get_action([], 'driserp.report_product_mark')

    @api.multi
    def print_picking(self):
        order_ids = []
        for wave in self:
            order_ids += [picking.sale_id.id for picking in wave.picking_ids]
        if not order_ids:
            raise UserError(_('Nothing to print.'))
        return self.env["report"].with_context(active_ids=order_ids, active_model='sale.order').\
            get_action([], 'driserp.report_order_dris')

    def set_style(self, name, height, bold=False, ):
        style = xlwt.XFStyle()  # 初始化样式
        font = xlwt.Font()  # 为样式创建字体
        borders = xlwt.Borders()
        borders.left = 1
        borders.right = 1
        borders.top = 1
        borders.bottom = 1
        borders.bottom_colour = 0x3A
        al = xlwt.Alignment()
        al.horz = xlwt.Alignment.HORZ_CENTER  # 设置水平居中
        al.vert = xlwt.Alignment.VERT_CENTER  # 设置垂直居中
        al.wrap = xlwt.Alignment.WRAP_AT_RIGHT  # 设置文字可以换行
        style.alignment = al
        font.name = name
        font.bold = bold
        font.color_index = 4
        font.height = height
        style.font = font
        style.borders = borders
        return style

    raw_data = True

    @api.multi
    def print_pickings_excel(self, post):
        id = post.get('wave_id', False)
        if not id:
            return False
        else:
            workbook = xlwt.Workbook()
            ids = self.env['stock.picking.wave'].search([('id', '=', id)])
            pickings = self.env['stock.picking.wave'].browse(ids[0])
            for wave in pickings.picking_ids:
                order = wave.sale_id
                source_code = order.source_code  # 订单号
                location_details = order.location_details  # 仓库地址
                start_picking_time = ''  # 开始备货时间
                bill_time = ''  # 交单时间
                picking_person = ''  # 备货人
                order_start_time = order.order_start_time  # 订单日期
                deliverCenterName = order.deliverCenterName  # 分配机构

                worksheet = workbook.add_sheet('wave' + str(wave.id))
                worksheet.col(0).width = 0x0d00 - 2000
                worksheet.col(1).width = 0x0d00 + 2000
                worksheet.col(3).width = 0x0d00 + 15000
                worksheet.write_merge(0, 3, 0, 7,
                                      u"订单号： %s  开始备货时间:  %s  交单时间:  %s  备货人:  %s                 订单日期:  %s  分配机构:  %s  仓库地址:  %s" % (
                                          source_code, start_picking_time, bill_time, picking_person, order_start_time,
                                          deliverCenterName, location_details),
                                      self.set_style('Arial', 360, True))
                worksheet.write(4, 0, u'序号', self.set_style('Arial', 250, True))
                worksheet.write(4, 1, u'69码', self.set_style('Arial', 250, True))
                worksheet.write(4, 2, u'商品编码', self.set_style('Arial', 250, True))
                worksheet.write(4, 3, u'商品名称', self.set_style('Arial', 250, True))
                worksheet.write(4, 4, u'采购数量', self.set_style('Arial', 250, True))
                worksheet.write(4, 5, u'实发数量', self.set_style('Arial', 250, True))
                worksheet.write(4, 6, u'核算箱数', self.set_style('Arial', 250, True))
                worksheet.write(4, 7, u'编箱号码', self.set_style('Arial', 250, True))

                num = 1
                row = 5
                base_style = xlwt.easyxf('align: wrap yes')
                for line in order.order_line:
                    box_no = ''
                    for box in line.box_ids:
                        box_no += str(box.box_no) + ","
                    item = line.item_id
                    barcode = item.barcode  # 69码
                    sku = item.item_sku  # 商品编码
                    name = item.name  # 商品名称
                    originalNum = line.originalNum  # 采购数量
                    factnum = line.actualNum  # 实发数量
                    checkbox = line.originalNum  # 核算箱数
                    boxNum = box_no  # 编箱号码
                    worksheet.write(row, 0, num, base_style)
                    worksheet.write(row, 1, barcode, base_style)
                    worksheet.write(row, 2, sku, base_style)
                    worksheet.write(row, 3, name, base_style)
                    worksheet.write(row, 4, originalNum, base_style)
                    worksheet.write(row, 5, factnum, base_style)
                    worksheet.write(row, 6, checkbox, base_style)
                    worksheet.write(row, 7, boxNum, base_style)
                    row += 1
                    num += 1

            fp = StringIO()
            workbook.save(fp) 
            fp.seek(0)
            data = fp.read()
            fp.close()
            return data

    @api.multi
    def print_product_excel(self, post):
        id = post.get('wave_id', False)
        if not id:
            return False
        else:
            ids = self.env['stock.picking.wave'].search([('id', '=', id)])
            picking = self.env['stock.picking.wave'].browse(ids[0])

            workbook = xlwt.Workbook()
            worksheet = workbook.add_sheet('wave')
            worksheet.col(0).width = 0x0d00 + 15000

            worksheet.write_merge(0, 3, 0, 2, u'名称：  %s   负责人：  %s' % (picking.name, picking.user_id.display_name),
                                  self.set_style('Arial', 360, True))
            worksheet.write(4, 0, u'产品', self.set_style('Arial', 250, True))
            worksheet.write(4, 1, u'数量', self.set_style('Arial', 250, True))
            worksheet.write(4, 2, u'单位', self.set_style('Arial', 250, True))

            row = 5
            base_style = xlwt.easyxf('align: wrap yes')
            for line in picking.product_line:
                product = line.product_id.product_tmpl_id.name  # 产品
                qty = line.product_qty  # 数量
                uom = line.product_uom.name  # 单位
                worksheet.write(row, 0, product, base_style)
                worksheet.write(row, 1, qty, base_style)
                worksheet.write(row, 2, uom, base_style)
                row += 1

            fp = StringIO()
            workbook.save(fp)
            fp.seek(0)
            data = fp.read()
            fp.close()
            return data

    @api.multi
    def print_product_mark_excel(self, post):
        id = post.get('wave_id', False)
        if not id:
            return False
        else:
            ids = self.env['stock.picking.wave'].search([('id', '=', id)])
            picking = self.env['stock.picking.wave'].browse(ids[0])

            workbook = xlwt.Workbook()
            worksheet = workbook.add_sheet('wave')
            worksheet.col(1).width = 0x0d00 + 15000

            worksheet.write_merge(0, 3, 0, 3, u'名称：  %s   负责人：  %s' % (picking.name, picking.user_id.display_name),
                                  self.set_style('Arial', 360, True))
            worksheet.write(4, 0, u'大头笔', self.set_style('Arial', 250, True))
            worksheet.write(4, 1, u'产品', self.set_style('Arial', 250, True))
            worksheet.write(4, 2, u'数量', self.set_style('Arial', 250, True))
            worksheet.write(4, 3, u'单位', self.set_style('Arial', 250, True))

            row = 5
            base_style = xlwt.easyxf('align: wrap yes')
            for line in picking.mark_line:
                name = line.name  # 大头笔
                product = line.product_id.product_tmpl_id.name  # 产品
                qty = line.product_qty  # 数量
                uom = line.product_uom.name  # 单位
                worksheet.write(row, 0, name, base_style)
                worksheet.write(row, 1, product, base_style)
                worksheet.write(row, 2, qty, base_style)
                worksheet.write(row, 3, uom, base_style)
                row += 1

            fp = StringIO()
            workbook.save(fp)
            fp.seek(0)
            data = fp.read()
            fp.close()
            return data


class DPickingToWave(models.TransientModel):
    _name = 'stock.picking.to.wave'
    _inherit = 'stock.picking.to.wave'

    @api.multi
    def attach_pickings(self):
        # use active_ids to add picking line to the selected wave
        self.ensure_one()
        picking_ids = self.env.context.get('active_ids')
        wave = self.wave_id
        if picking_ids:
            for picking_id in picking_ids:
                picking = self.env['stock.picking'].browse(picking_id)
                if not picking.direct_group == wave.direct_group:
                    raise UserError(_("拣货单 %s 与波次 %s 面向人群不同！") % (picking.name, wave.name))
        res = self.env['stock.picking'].browse(picking_ids).write({'wave_id': self.wave_id.id})
        wave.compute_product_line()
        return res
