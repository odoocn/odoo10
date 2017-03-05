# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from odoo import api, fields, models, _


class OrderTrack(models.Model):
    _name = "order.track"

    name = fields.Char(string=u'单号', required=True)
    type = fields.Selection([('sale', '销售订单'), ('purchase', '采购订单')], string=u'类型')
    sale_id = fields.Many2one('sale.order', string=u'销售订单')
    purchase_id = fields.Many2one('purchase.order', string=u'采购订单')

    order_line = fields.One2many('order.track.line', 'track_id', string=u'明细')
    danger = fields.Boolean(default=False, compute='compute_danger', store=True)

    remark = fields.Text(string=u'备注')

    @api.depends('order_line')
    def compute_danger(self):
        for r in self:
            flag = False
            for line in r.order_line:
                if not line.actualNum == line.confirmNum:
                    flag = True
                    break
            if flag:
                r.danger = True
            else:
                r.danger = False


class OrderTrackLine(models.Model):
    _name = "order.track.line"

    track_id = fields.Many2one('order.track')
    product_id = fields.Many2one('product.product', string=u'产品')
    item_id = fields.Many2one('ecps.items', string=u'商品')
    originNum = fields.Float('原始数量')
    confirmNum = fields.Float('确认数量')
    actualNum = fields.Float('实收数量')
    remark = fields.Text('备注')
