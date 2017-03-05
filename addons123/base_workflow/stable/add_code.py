# coding:utf-8
from odoo import api, fields, models, _


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    code = fields.Char('内部编码', compute='get_code')
    change_tax = fields.Many2one('account.tax', string=u'调整税金')

    @api.onchange('change_tax')
    def _onchange_tax(self):
        for invoice_line in self.invoice_line_ids:
            invoice_line.write({'invoice_line_tax_ids': [(6, 0, self.change_tax.ids)]})
        self.change_tax = None

    @api.one
    def get_code(self):
        code = ''
        if self.type == 'out_invoice':
            a = []
            for line in self.invoice_line_ids:
                if len(line.sale_line_ids) > 0:
                    if line.sale_line_ids[0].order_id.order_code and str(
                            line.sale_line_ids[0].order_id.order_code) not in a:
                        a.append(str(line.sale_line_ids[0].order_id.order_code))
            code = ','.join(a)
        elif self.type == 'in_invoice':
            a = []
            for line in self.invoice_line_ids:
                if line.purchase_id.order_code and str(line.purchase_id.order_code) not in a:
                    a.append(str(line.purchase_id.order_code))
            code = ','.join(a)
        self.code = code
