# -*- coding: utf-8 -*-
from odoo import fields, models


class inventory_cost_product(models.Model):

    _inherit = "product.template"
    inventory_method = fields.Selection([('moving', '移动加权平均法'), ('all', '全月一次加权平均法')], u'成本核算方式', default="moving")
