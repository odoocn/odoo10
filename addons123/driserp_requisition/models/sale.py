# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import time
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero

_logger = logging.getLogger(__name__)


class OSaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'

    @api.depends('requisition_ids')
    def compute_requisition(self):
        for po in self:
            po.requisition_count = len(po.requisition_ids)

    requisition_count = fields.Integer(string=u'开票申请', compute=compute_requisition)
    requisition_ids = fields.Many2many('requisition.invoice', string=u'开票申请')
    payment_ids = fields.One2many('account.payment', 'sale_id', string=u'付款')
    order_paid = fields.Monetary(string=u'订单已收', compute='compute_paid')

    # ===zhy
    @api.depends('invoice_ids', 'payment_ids')
    def compute_paid(self):
        for r in self:
            r.order_paid = r.get_paid_amount()[0]
        return True

    @api.one
    def get_paid_amount(self):
        paid = 0.0000
        for invoice in self.invoice_ids:
            part_amount = 0.0000
            if invoice.state in ('open', 'paid'):
                for line in invoice.invoice_line_ids:
                    if len(line.sale_line_ids) > 0 and line.sale_line_ids[0].order_id.id == self.id:
                        part_amount += line.price_unit * line.quantity
                precision = self.env['decimal.precision'].precision_get('Product Price')
                if not float_is_zero(invoice.amount_total_company_signed, precision_digits=precision):
                    paid += abs(part_amount / invoice.amount_total_company_signed) * \
                            (invoice.amount_total_company_signed - invoice.residual_company_signed)
        # 收款未调节
        for move_line in self.env['account.move.line'].search([
            ('sale_id', '=', self.id), ('credit', '>', 0), ('debit', '=', 0),
            ('reconciled', '=', False), ('amount_residual', '!=', 0.0)
        ]):
            paid += move_line.credit
        # 退款未调节
        for move_line in self.env['account.move.line'].search([
            ('sale_id', '=', self.id), ('credit', '=', 0), ('debit', '>', 0),
            ('reconciled', '=', False), ('amount_residual', '!=', 0.0)
        ]):
            paid -= move_line.debit
        return paid
        # ---zhy


class SaleAdvancePaymentInv(models.TransientModel):
    _name = "sale.advance.payment.inv"
    _inherit = "sale.advance.payment.inv"

    @api.multi
    def create_invoices(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))

        if self.advance_payment_method == 'delivered':
            sale_orders.action_invoice_create()
        elif self.advance_payment_method == 'all':
            sale_orders.action_invoice_create(final=True)
        else:
            # Create deposit product if necessary
            if not self.product_id:
                vals = self._prepare_deposit_product()
                self.product_id = self.env['product.product'].create(vals)
                self.env['ir.values'].sudo().set_default('sale.config.settings', 'deposit_product_id_setting',
                                                         self.product_id.id)

            sale_line_obj = self.env['sale.order.line']
            for order in sale_orders:
                if self.advance_payment_method == 'percentage':
                    amount = order.amount_untaxed * self.amount / 100
                else:
                    amount = self.amount
                if self.product_id.invoice_policy != 'order':
                    raise UserError(_(
                        'The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
                if self.product_id.type != 'service':
                    raise UserError(_(
                        "The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
                so_line = sale_line_obj.create({
                    'name': _('Advance: %s') % (time.strftime('%m %Y'),),
                    'price_unit': amount,
                    'product_uom_qty': 0.0,
                    'order_id': order.id,
                    'discount': 0.0,
                    'product_uom': self.product_id.uom_id.id,
                    'product_id': self.product_id.id,
                    'tax_id': [(6, 0, self.product_id.taxes_id.ids)],
                })
                self._create_invoice(order, so_line, amount)
        if self._context.get('open_invoices', False):
            return sale_orders.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}