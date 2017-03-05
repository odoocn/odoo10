# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import logging


class ReturnOrder(models.Model):
    _name = "return.order"

    name = fields.Char(string=u'退货单号')
    source_shop = fields.Many2one('ecps.shop', string=u'店铺')
    state = fields.Selection([('draft', '草稿'), ('confirmed', '已确认'), ('done', '完成')], string=u'状态', default='draft')

    provider_code = fields.Char(string=u'供应商编码')
    provider_name = fields.Char(string=u'供应商名称')

    from_place = fields.Char(string=u'退货地点')
    to_place = fields.Char(string=u'退货目的地')
    from_address = fields.Char(string=u'退货地址')
    from_phone = fields.Char(string=u'退货人联系电话')
    from_name = fields.Char(string=u'退货人姓名')

    order_state = fields.Char(string=u'退货单状态')

    balance_state = fields.Char(string=u'退货结算状态名称')
    balance_date = fields.Date(string=u'退货单结算时间')

    remark = fields.Text(string=u'备注')
    stock_name = fields.Char(string=u'商品库房名称')
    out_time = fields.Datetime(string=u'出库时间')
    total_price = fields.Float(string=u'总额', compute='compute_amount', store=True)
    # sale_id = fields.Many2one('sale.order', string=u'销售订单')
    order_id = fields.Many2one('stock.picking', string=u'退货单')
    line_ids = fields.One2many('return.order.line', 'return_id', string=u'明细')

    @api.multi
    def confirm(self):
        self.write({'state': 'confirmed'})
        return True

    @api.model
    def _default_warehouse(self):
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_id)])
        return warehouse[:1]

    @api.multi
    def return_item(self):
        new_return = self.env['stock.picking'].create({'picking_type_id': self._default_warehouse().re_type_id.id,
                                                       'location_id': self._default_warehouse().re_type_id.default_location_src_id.id,
                                                       'location_dest_id': self._default_warehouse().re_type_id.default_location_dest_id.id,
                                                       })
        self.order_id = new_return.id
        for line in self.line_ids:
            new_return.move_lines.add({
                'product_id': line.product_id.id,
                'picking_id': new_return.id,
                'ordered_qty': line.return_actual,
                'product_qty': line.return_actual,
                'product_uom_qty': line.return_actual,

            })
        return self.env['tools.alert.dialog'].new_alert(msg=u'完成')

    @api.depends('line_ids')
    def compute_amount(self):
        for r in self:
            amount = 0
            for line in r.line_ids:
                amount += line.total_price
            r.total_price = amount


class ReturnOrderLine(models.Model):
    _name = 'return.order.line'

    return_id = fields.Many2one('return.order', string=u'退货单')
    product_id = fields.Many2one('product.product', string=u'产品', compute='compute_product', store=True)
    item = fields.Many2one('ecps.items', string=u'退货商品')
    return_num = fields.Float(string=u'退货数量')
    return_price = fields.Float(string=u'退货价格')
    return_actual = fields.Float(string=u'实际退货数量')
    total_price = fields.Float(string=u'总额', readonly=True, compute='compute_amount', store=True)

    @api.depends('return_num', 'return_price')
    def compute_amount(self):
        for r in self:
            r.total_price = r.return_actual * r.return_price

    @api.depends('item')
    def compute_product(self):
        for r in self:
            if r.item and r.item.product_id:
                r.product_id = r.item.product_id
