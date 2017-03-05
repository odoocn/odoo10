from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class ReturnVendorLine(models.Model):
    _inherit = 'return.vendor.line'

    # @api.onchange('return_qty')
    # def _onchange_return_qty(self):
    #     if not self.return_qty <= self.product_qty:
    #         raise ValueError('error')