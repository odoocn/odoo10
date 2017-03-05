# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from datetime import datetime, timedelta
from odoo import SUPERUSER_ID
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import json

_logger = logging.getLogger(__name__)


class EAccountPayment(models.Model):
    _name = "account.payment"
    _inherit = "account.payment"

    purchase_id = fields.Many2one('purchase.order', string=u'采购订单')
    sale_id = fields.Many2one('sale.order', string=u'销售订单')
    requisition_id = fields.Many2one('requisition.pay', string=u'付款申请')

    @api.onchange('requisition_id')
    def on_change_requisition_id(self):
        if self.requisition_id:
            self.journal_id = self.requisition_id.journal_id.id
            self.amount = self.requisition_id.req_amount
            self.purchase_id = self.requisition_id.purchase_id.id

    @api.onchange('purchase_id')
    def on_change_purchase_id(self):
        if self.purchase_id and not self.partner_id:
            self.partner_id = self.purchase_id.partner_id.id

    @api.onchange('sale_id')
    def on_change_sale_id(self):
        if self.sale_id and not self.partner_id:
            self.partner_id = self.sale_id.partner_id.id

    @api.multi
    def post(self):
        """ Create the journal items for the payment and update the payment's state to 'posted'.
            A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
            and another in the destination reconciliable account (see _compute_destination_account_id).
            If invoice_ids is not empty, there will be one reconciliable move line per invoice to reconcile with.
            If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
        """
        for rec in self:

            if rec.state != 'draft':
                raise UserError(
                    _("Only a draft payment can be posted. Trying to post a payment in state %s.") % rec.state)

            if any(inv.state != 'open' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

            # Use the right sequence to set the name
            if rec.payment_type == 'transfer':
                sequence_code = 'account.payment.transfer'
            else:
                if rec.partner_type == 'customer':
                    if rec.payment_type == 'inbound':
                        sequence_code = 'account.payment.customer.invoice'
                    if rec.payment_type == 'outbound':
                        sequence_code = 'account.payment.customer.refund'
                if rec.partner_type == 'supplier':
                    if rec.payment_type == 'inbound':
                        sequence_code = 'account.payment.supplier.refund'
                    if rec.payment_type == 'outbound':
                        sequence_code = 'account.payment.supplier.invoice'
            rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(
                sequence_code)

            # Create the journal entry
            amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
            move = rec._create_payment_entry(amount)

            # In case of a transfer, the first journal entry created debited the source liquidity account and credited
            # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
            if rec.payment_type == 'transfer':
                transfer_credit_aml = move.line_ids.filtered(
                    lambda r: r.account_id == rec.company_id.transfer_account_id)
                transfer_debit_aml = rec._create_transfer_entry(amount)
                (transfer_credit_aml + transfer_debit_aml).reconcile()

            if rec.purchase_id:
                move.write({'purchase_id': rec.purchase_id.id})

            if rec.sale_id:
                move.write({'sale_id': rec.sale_id.id})

            rec.state = 'posted'


class EAccountRegPayment(models.TransientModel):
    _inherit = "account.register.payments"

    reg_id = fields.Many2one("requisition.pay", string=u'付款申请')

    @api.multi
    def create_payment(self):
        payment = self.env['account.payment'].create(self.get_payment_vals())
        payment.post()
        if self.reg_id:
            self.reg_id.write({'payment': payment.id})
        return {'type': 'ir.actions.act_window_close'}

    @api.onchange('reg_id')
    def onchange_reg_id(self):
        if self.reg_id:
            self.journal_id = self.reg_id.journal_id
            self.amount = self.reg_id.req_amount


class EAccountMove(models.Model):
    _name = "account.move"
    _inherit = 'account.move'

    purchase_id = fields.Many2one('purchase.order', string=u'采购订单')
    sale_id = fields.Many2one('sale.order', string=u'销售订单')


class EAccountMoveLine(models.Model):
    _name = "account.move.line"
    _inherit = "account.move.line"

    @api.depends('move_id.purchase_id', 'move_id.sale_id')
    def compute_order(self):
        for r in self:
            r.sale_id = r.move_id.sale_id
            r.purchase_id = r.move_id.purchase_id

    purchase_id = fields.Many2one('purchase.order', string=u'采购订单', compute=compute_order, store=True)
    sale_id = fields.Many2one('sale.order', string=u'销售订单', compute=compute_order, store=True)


class EAccountInvoice(models.Model):
    _name = 'account.invoice'
    _inherit = 'account.invoice'

    invoice_type = fields.Selection([('normal', '普通发票'), ('special', '专用发票')], string=u'发票类型', default='special', required=True)
    invoice_code = fields.Char(string=u'票号')

    @api.one
    def _get_outstanding_info_JSON(self):
        self.outstanding_credits_debits_widget = json.dumps(False)
        if self.state == 'open':
            domain = [('account_id', '=', self.account_id.id),
                      ('partner_id', '=', self.env['res.partner']._find_accounting_partner(self.partner_id).id),
                      ('reconciled', '=', False), ('amount_residual', '!=', 0.0)]

            if self.type in ('in_invoice', 'in_refund'):
                temp = []
                for line in self.invoice_line_ids:
                    temp.append(line.purchase_id.id)
                domain.extend(['|', ('purchase_id', 'in', temp), ('purchase_id', '=', False)])

            if self.type in ('out_invoice', 'out_refund'):
                temp = []
                for line in self.invoice_line_ids:
                    if len(line.sale_line_ids):
                        temp.append(line.sale_line_ids[0].order_id.id)
                domain.extend(['|', ('sale_id', 'in', temp), ('sale_id', '=', False)])

            if self.type in ('out_invoice', 'in_refund'):
                domain.extend([('credit', '>', 0), ('debit', '=', 0)])
                type_payment = _('Outstanding credits')
            else:
                domain.extend([('credit', '=', 0), ('debit', '>', 0)])
                type_payment = _('Outstanding debits')
            info = {'title': '', 'outstanding': True, 'content': [], 'invoice_id': self.id}
            lines = self.env['account.move.line'].search(domain)
            currency_id = self.currency_id
            if len(lines) != 0:
                for line in lines:
                    # get the outstanding residual value in invoice currency
                    if line.currency_id and line.currency_id == self.currency_id:
                        amount_to_show = abs(line.amount_residual_currency)
                    else:
                        amount_to_show = line.company_id.currency_id.with_context(date=line.date).compute(
                            abs(line.amount_residual), self.currency_id)
                    if float_is_zero(amount_to_show, precision_rounding=self.currency_id.rounding):
                        continue
                    info['content'].append({
                        'journal_name': line.ref or line.move_id.name,
                        'amount': amount_to_show,
                        'currency': currency_id.symbol,
                        'id': line.id,
                        'position': currency_id.position,
                        'digits': [69, self.currency_id.decimal_places],
                    })
                info['title'] = type_payment
                self.outstanding_credits_debits_widget = json.dumps(info)
                self.has_outstanding = True
