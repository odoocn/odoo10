# -*- coding: utf-8 -*-
from odoo import api, _, fields, models


class type_account_relation(models.Model):
    _name = "type.account.relation"

    name = fields.Char(u"收发类型")  # 入库类型
    purchase_in = fields.Selection([('purchase_in', '采购入库'),
                                    ('other_in', '其他入库'),
                                    ('sale_out', '销售出库'),
                                    ('other_out', '其他出库'),
                                    ('internal_transfers', '内部调拨')], string=u"出入库类型")


class purchase_sale_type(models.Model):
    _name = "purchase.sale.type"

    name = fields.Char(u'分类名称')
    type = fields.Selection([('purchase', '采购类型'), ('sale', '销售类型')], u'类别')
    send_receive_type = fields.Many2one('type.account.relation', u'收发类型')


class inherit_purchase_type(models.Model):
    _inherit = "purchase.order"

    @api.model
    def _default_type(self):
        res = self.env['purchase.sale.type'].search([('type', '=', 'purchase')])
        if res:
            return res[0]
        else:
            return False

    purchase_type = fields.Many2one('purchase.sale.type', u'采购类型', domain=[('type', '=', 'purchase')], required=True, default=_default_type)


class inherit_sale_type(models.Model):
    _inherit = "sale.order"

    @api.model
    def _default_type(self):
        res = self.env['purchase.sale.type'].search([('type', '=', 'sale')])
        if res:
            return res[0]
        else:
            return False

    sale_type = fields.Many2one('purchase.sale.type', u'销售类型', domain=[('type', '=', 'sale')], required=True, default=_default_type)
