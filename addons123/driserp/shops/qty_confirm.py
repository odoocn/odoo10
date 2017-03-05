# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from odoo import api, fields, models, _


class QtyConfirmLine(models.Model):
    _name = 'qty.confirm.line'

    confirm_id = fields.Many2one('qty.confirm', string=u'回告ID')
    item_id = fields.Many2one('ecps.items', string=u'商品')
    product_id = fields.Many2one('product.product', string=u'产品', required=True)
    availableNum = fields.Float(related='product_id.qty_available', string=u'在手数量')
    forecastNum = fields.Float(related='product_id.virtual_available', string=u'预测数量')
    originalNum = fields.Float(string=u'原始数量')
    confirmedNum = fields.Float(string=u'确认数量', required=True)
    deliverCenterId = fields.Integer(string=u'配送中心ID')
    deliverCenterName = fields.Char(string=u'配送中心名称')


class QtyConfirm(models.Model):
    _name = 'qty.confirm'

    name = fields.Char(string=u'编号')
    order_id = fields.Many2one('sale.order', string=u'销售订单', readonly=True)
    line_ids = fields.One2many('qty.confirm.line', 'confirm_id', string=u'明细')
    description = fields.Text(string=u'备注')
    delivery_time = fields.Datetime(string=u'预计发货时间')
    r_success = fields.Boolean(string=u'返回成功', default=False)

    state = fields.Selection([('draft', '草稿'), ('confirmed', '已确认'), ('done', '完成')],
                             string=u'状态', default='draft')

    @api.multi
    def button_confirm(self):
        self.ensure_one()
        self.write({'state': 'confirmed'})
        return True

    @api.multi
    def button_send(self):
        self.ensure_one()
        link_api = self.order_id.source_shop.plate_id.get_api(self.order_id.source_shop.access_token.encode('utf-8'))[0]
        item = []
        num = []
        center = []
        for line in self.line_ids:
            item.append(str(line.item_id.item_sku))
            num.append(str(line.confirmedNum))
            center.append(str(line.deliverCenterId))
        res = link_api.order_confirm(self.order_id.source_code, item, center, num, self.delivery_time)
        if res['code'] == 0:
            self.write({'r_success': True, 'state': 'done'})
            self.order_id.write({'return_state': True})
            self.order_id.syn_order()
            # self.order_id.action_confirm()
        else:
            raise UserWarning(_('回告失败！'))
        return True

    @api.multi
    def button_done(self):
        self.ensure_one()
        self.write({'state': 'done'})
        return True
