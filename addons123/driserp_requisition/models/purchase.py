# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from odoo import api, _, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_is_zero

_logger = logging.getLogger(__name__)


class DPurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = 'purchase.order'

    @api.depends('requisition_ids')
    def compute_requisition(self):
        for po in self:
            po.requisition_count = len(po.requisition_ids)

    requisition_count = fields.Integer(string=u'付款申请', compute=compute_requisition)
    requisition_ids = fields.Many2many('requisition.pay', string=u'付款申请')
    payment_ids = fields.One2many('account.payment', 'purchase_id', string=u'付款')
    order_paid = fields.Monetary(string=u'订单已付', compute='compute_paid')

    @api.multi
    def unlink(self):
        for po in self:
            if len(po.requisition_ids) > 0:
                raise ValidationError(_("已生成付款申请的订单不可删除"))
        return super(DPurchaseOrder, self).unlink()

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
                    if line.purchase_id and line.purchase_id.id == self.id:
                        part_amount += line.price_unit * line.quantity
                precision = self.env['decimal.precision'].precision_get('Product Price')
                if not float_is_zero(invoice.amount_total_company_signed, precision_digits=precision):
                    paid += abs(part_amount / invoice.amount_total_company_signed) * \
                            (invoice.amount_total_company_signed - invoice.residual_company_signed)
        # 退款未调节
        for move_line in self.env['account.move.line'].search([
            ('purchase_id', '=', self.id), ('credit', '>', 0), ('debit', '=', 0),
            ('reconciled', '=', False), ('amount_residual', '!=', 0.0)
        ]):
            paid -= move_line.credit
        # 付款未调节
        for move_line in self.env['account.move.line'].search([
            ('purchase_id', '=', self.id), ('credit', '=', 0), ('debit', '>', 0),
            ('reconciled', '=', False), ('amount_residual', '!=', 0.0)
        ]):
            paid += move_line.debit
        return paid
    # ---zhy
