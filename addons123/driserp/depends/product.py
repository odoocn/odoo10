# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class DProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'

    uom_stock_id = fields.Many2one('product.uom', string=u'装箱单位')

    @api.constrains('uom_id', 'uom_stock_id')
    def _check_stock_uom(self):
        if any(product.uom_stock_id and product.uom_id.category_id.id != product.uom_stock_id.category_id.id for product in self):
            raise ValidationError(_('错误：默认的计量单位和装箱单位必须是相同的类别'))
        return True

    @api.constrains('uom_stock_id')
    def _check_stock_bigger(self):
        if any(product.uom_stock_id and not product.uom_stock_id.uom_type == 'bigger' for product in self):
            raise ValidationError(_('错误：装箱单位类型应为大于参考单位'))
        return True
