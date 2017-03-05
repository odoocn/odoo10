# -*- coding: utf-8 -*-
from odoo import api, _, fields, models


class inventory_cost_stock_picking(models.Model):
    _inherit = "stock.picking"

    send_receive_type = fields.Many2one('type.account.relation', string=u'收发类型', required=True, readonly=True,
                                        states={'draft': [('readonly', False)]})


class inventory_cost_stock_move(models.Model):

    _inherit = "stock.move"

    @api.depends('sale_id', 'purchase_id')
    def _name_get_partner(self):
        for op in self:
            if op.sale_id:
                op.supplier_or_customer = op.sale_id.partner_id.name
            if op.purchase_id:
                op.supplier_or_customer = op.purchase_id.partner_id.name

    sale_line_id = fields.Many2one('sale.order.line', string=u'销售订单行', readonly=True)
    sale_id = fields.Many2one('sale.order', string=u'销售订单', readonly=True)
    purchase_id = fields.Many2one("purchase.order", string='采购订单', readonly=True)
    supplier_or_customer = fields.Char(string=u'业务伙伴', compute='_name_get_partner', store=True)
    account_type = fields.Selection([('0', '暂估'), ('1', '已结算'), ('2', '已记账')], u'核算类型', default="0")
    handle_flg = fields.Boolean(u'是否处理')
    send_receive_type = fields.Many2one('type.account.relation', string=u'收发类型', compute="compute_type", store=True)
    estimated_price = fields.Float(u'预估单价', digits=(16, 2))  # 入库单预存的采购订单的单价
    estimated_amount = fields.Float(u'预估金额', digits=(16, 2))  # 入库单预存的采购订单的单价
    cost_test = fields.Float(u'草稿单价', digits=(16, 4))   # 保存结算单是预存的单价，结算后将该值赋给单价字段
    cost = fields.Float(u'单价', digits=(16, 4))  # 未结算移库单：采购订单含税单价；结算入库单据：成本；出库单据：销售单价
    amount = fields.Float(u'金额', digits=(16, 4))  # 未结算移库单：采购订单含税总金额；结算入库单据：成本总额；出库单据：销售总额

    @api.depends("picking_id")
    def compute_type(self):
        for r in self:
            if r.picking_id and r.picking_id.send_receive_type:
                r.send_receive_type = r.picking_id.send_receive_type.id

    @api.model
    def create(self, values):
        result = super(inventory_cost_stock_move, self).create(values)
        # 获取收发类型
        if result.purchase_line_id:
            send_receive_type = result.purchase_line_id.order_id.purchase_type.send_receive_type
            value = {
                "purchase_id": result.purchase_line_id.order_id,
                "send_receive_type": send_receive_type,
                'estimated_price': result.purchase_line_id.price_unit,
                'estimated_amount': result.purchase_line_id.price_total
            }
            result.update(value)
        else:
            send_receive_type = result.procurement_id.sale_line_id.order_id.sale_type.send_receive_type
            value = {
                "sale_id": result.procurement_id.sale_line_id.order_id,
                "sale_line_id": result.procurement_id.sale_line_id,
                "send_receive_type": send_receive_type,
                'estimated_price': result.procurement_id.sale_line_id.price_unit,
                'amount': result.procurement_id.sale_line_id.price_total
            }
            result.update(value)
        return result
