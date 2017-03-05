# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError, ValidationError
import datetime
import urllib2
import json
import time
import logging

_logger = logging.getLogger(__name__)


class RequisitionPay(models.Model):
    # 供应商帐单 付款申请单

    _name = "requisition.pay"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.depends('purchase_ids')
    def _compute_amount(self):
        for r in self:
            amount = 0
            for p in r.purchase_ids:
                amount += p.amount_total
            r.amount = amount

    @api.depends('payment_ids')
    def _compute_payment(self):
        for r in self:
            if len(r.payment_ids):
                r.payment = r.payment_ids[0]
            else:
                r.payment = False

    @api.depends('payment', 'payment.state', 'account_cancel')
    def _compute_undone(self):
        for r in self:
            if (r.payment and r.payment.state != 'draft') or r.account_cancel:
                r.undone_state = False
            else:
                r.undone_state = True

    @api.depends('purchase_ids')
    def _compute_last_amount(self):
        for r in self:
            total = 0.0000
            amount = 0.0000
            for po in r.purchase_ids:
                total += po.amount_total
                amount += po.get_paid_amount()[0]
            r.last_amount = total - amount
        return True

    name = fields.Char(string=u'说明', required=True)
    create_uid = fields.Many2one('res.users', string='Created by', readonly=True)
    # 唯一时的采购订单
    purchase_id = fields.Many2one('purchase.order', string=u'采购订单', compute='compute_purchase_only')
    purchase_ids = fields.Many2many('purchase.order', string=u'采购订单')
    state = fields.Selection([('draft', '草稿'), ('cancel', '取消'), ('checking', '审核中'), ('reject', '驳回'), ('done', '完成')],
                             string=u'审核状态', default='draft')
    currency_id = fields.Many2one('res.currency', string=u'货币', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    req_amount = fields.Monetary(string=u'本次申请金额')
    amount = fields.Monetary(string=u'全额', compute=_compute_amount)
    last_amount = fields.Monetary(string=u'采购订单未付金额', compute=_compute_last_amount)
    paid = fields.Monetary(string=u'本申请已付', related='payment.amount')
    undone_state = fields.Boolean(string=u'待办', default=True, compute=_compute_undone, store=True)

    payment_ids = fields.One2many("account.payment", 'requisition_id', string=u'付款单')
    payment = fields.Many2one('account.payment', string=u'付款单', compute=_compute_payment, store=True)

    vendor_id = fields.Many2one('res.partner', string=u'供应商', compute='compute_vendor', store=True)
    journal_id = fields.Many2one('account.journal', string=u'付款日记账', required=True,
                                 domain=[('type', 'in', ('bank', 'cash'))])

    description = fields.Text(string=u'备注')
    account_cancel = fields.Boolean(string=u'待办被取消', default=False)

    @api.multi
    def close_undone(self):
        return self.write({'account_cancel': True})

    @api.depends('purchase_ids')
    def compute_vendor(self):
        for r in self:
            if len(r.purchase_ids) > 0:
                r.vendor_id = r.purchase_ids[0].partner_id.id
        return True

    @api.multi
    @api.depends('name')
    def name_get(self):
        result = []
        for reg in self:
            name = reg.name
            if reg.req_amount:
                name += ': ' + formatLang(self.env, reg.req_amount, currency_obj=reg.currency_id)
            result.append((reg.id, name))
        return result

    @api.multi
    def view_bills(self):
        bills_ids = []
        for po in self.purchase_ids:
            for line in po.order_line:
                inv_lines = self.env['account.invoice.line'].search([('purchase_line_id', '=', line.id)])
                for inv_line in inv_lines:
                    if inv_line.invoice_id.id not in bills_ids:
                        bills_ids.append(inv_line.invoice_id.id)

        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_invoice_tree2')
        form_view_id = imd.xmlid_to_res_id('account.invoice_supplier_form')
        tree_view_id = imd.xmlid_to_res_id('account.invoice_supplier_tree')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[tree_view_id, 'tree'], [form_view_id, 'form']],
            'target': action.target,
            'res_model': action.res_model,
            'domain': "[['id','in',%s]]" % str(bills_ids),
            'context': "{'default_journal_id':%s}" % self.journal_id.id
        }

        return result

    @api.constrains('purchase_ids')
    def check_vendors(self):
        for r in self:
            vendors = []
            for p in r.purchase_ids:
                if p.partner_id.id not in vendors:
                    vendors.append(p.partner_id.id)
                if p.state not in ('purchase', 'done'):
                    raise ValidationError(_("不能添加未通过审核的采购订单"))
            if len(vendors) > 1:
                raise ValidationError(_("不能添加不同供应商的采购订单"))
        return True

    @api.depends('purchase_ids')
    def compute_purchase_only(self):
        for r in self:
            if len(r.purchase_ids) == 1:
                r.purchase_id = r.purchase_ids[0].id
            else:
                r.purchase_id = False

    @api.multi
    def finish(self):
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('driserp_requisition.action_requisition_all')
        form_view_id = imd.xmlid_to_res_id('driserp_requisition.requisition_pay_watch_view')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form']],
            'target': action.target,
            'res_model': action.res_model,
            'res_id': self.id,
        }
        return result

    @api.multi
    def create_bills(self):
        bills = self.env['account.invoice'].with_context(type='in_invoice', journal_type='purchase')\
            .create({'type': 'in_invoice',
                     'journal_type': 'purchase',
                     'partner_id': self.purchase_ids[0].partner_id.id})
        for po in self.purchase_ids:
            bills.purchase_id = po.id
            new_lines = self.env['account.invoice.line']
            for line in po.order_line:
                # Load a PO line only once
                if line in bills.invoice_line_ids.mapped('purchase_line_id'):
                    continue
                data = bills._prepare_invoice_line_from_po_line(line)
                data['invoice_id'] = bills.id
                new_line = new_lines.create(data)
                new_line._set_additional_fields(bills)

            bills.purchase_id = False

        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_invoice_tree2')
        form_view_id = imd.xmlid_to_res_id('account.invoice_supplier_form')

        result = {
            'name': action.name,
            'help': action.help,
            'view_type': 'form',
            'view_mode': 'form',
            'type': action.type,
            'view_id': form_view_id,
            'target': action.target,
            'res_model': action.res_model,
            'res_id': bills.id
        }

        return result


class RequisitionInvoice(models.Model):
    _name = 'requisition.invoice'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.depends('order_ids')
    def _compute_invoice(self):
        for r in self:
            r.invoice_status = 'no'
            amount = 0
            for o in r.order_ids:
                amount += o.amount_total
                if o.invoice_status == 'to invoice':
                    r.invoice_status = 'to invoice'
            r.order_amount = amount

    @api.depends('invoice_id', 'invoice_id.state', 'account_cancel')
    def _compute_undone(self):
        for r in self:
            if (r.invoice_id and r.invoice_id.state in ('open', 'paid')) or r.account_cancel:
                r.undone_state = False
            else:
                r.undone_state = True

    name = fields.Char(string=u'说明')
    create_uid = fields.Many2one('res.users', string='Created by', readonly=True)
    # order_id = fields.Many2one('sale.order', string=u'销售订单')
    order_ids = fields.Many2many('sale.order', string=u'销售订单')
    state = fields.Selection([('draft', '草稿'), ('cancel', '取消'), ('checking', '审核中'), ('reject', '驳回'), ('done', '完成')],
                             string=u'审核状态', default='draft')
    invoice_id = fields.Many2one('account.invoice', string=u'客户发票')
    currency_id = fields.Many2one('res.currency', string=u'货币', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    req_amount = fields.Monetary(string=u'本次申请金额')
    order_amount = fields.Monetary(string=u'订单总额', compute=_compute_invoice)
    invoice_amount = fields.Monetary(string=u'已开票金额')
    description = fields.Text(string=u'备注')
    invoice_status = fields.Char(compute=_compute_invoice)
    undone_state = fields.Boolean(string=u'待办', default=True, compute=_compute_undone, store=True)
    customer = fields.Many2one('res.partner', string=u'客户', compute='compute_customer', store=True)
    account_cancel = fields.Boolean(string=u'待办被取消', default=False)

    @api.multi
    def close_undone(self):
        return self.write({'account_cancel': True})

    @api.multi
    @api.depends('name')
    def name_get(self):
        result = []
        for reg in self:
            name = reg.name
            if reg.req_amount:
                name += ': ' + formatLang(self.env, reg.req_amount, currency_obj=reg.currency_id)
            result.append((reg.id, name))
        return result

    @api.depends('order_ids')
    def compute_customer(self):
        for r in self:
            if len(r.order_ids) > 0:
                r.customer = r.order_ids[0].partner_id.id
        return True

    @api.constrains('order_ids')
    def check_vendors(self):
        for r in self:
            customer = []
            for o in r.order_ids:
                if o.partner_id.id not in customer:
                    customer.append(o.partner_id.id)
                if o.state not in ('sale', 'done'):
                    raise ValidationError(_("不能添加未通过审核的销售订单"))
            if len(customer) > 1:
                raise ValidationError(_("不能添加不同客户的销售订单"))
        return True

    @api.multi
    def finish(self):
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('driserp_requisition.action_requisition_invoice_so')
        form_view_id = imd.xmlid_to_res_id('driserp_requisition.requisition_invoice_watch_view')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form']],
            'target': action.target,
            'res_model': action.res_model,
            'res_id': self.id,
        }
        return result


class SaleAdvancePaymentInv(models.TransientModel):
    _name = "sale.advance.payment.inv"
    _inherit = "sale.advance.payment.inv"

    @api.model
    def _count_req(self):
        if self._context.get('req_id', []):
            return len(self.env['requisition.invoice'].browse(self._context.get('req_id')).order_ids)
        else:
            return len(self._context.get('active_ids', []))

    @api.model
    def _get_advance_payment_method_req(self):
        if self._count_req() == 1:
            sale_obj = self.env['sale.order']
            req_obj = self.env['requisition.invoice']
            if self._context.get('req_id', []):
                order = req_obj.browse(self._context.get('req_id')).order_ids[0]
            else:
                order = sale_obj.browse(self._context.get('active_ids'))[0]
            if all([line.product_id.invoice_policy == 'order' for line in order.order_line]) or order.invoice_count:
                return 'all'
        return 'delivered'

    advance_payment_method = fields.Selection([
        ('delivered', 'Invoiceable lines'),
        ('all', 'Invoiceable lines (deduct down payments)'),
        ('percentage', 'Down payment (percentage)'),
        ('fixed', 'Down payment (fixed amount)')
    ], string='What do you want to invoice?', default=_get_advance_payment_method_req, required=True)

    count = fields.Integer(default=_count_req, string='# of Orders')

    req_id = fields.Many2one('requisition.invoice', string='Requisition')

    @api.multi
    def _create_invoice(self, order, so_line, amount):
        inv_obj = self.env['account.invoice']
        ir_property_obj = self.env['ir.property']

        account_id = False
        if self.product_id.id:
            account_id = self.product_id.property_account_income_id.id
        if not account_id:
            prop = ir_property_obj.get('property_account_income_categ_id', 'product.category')
            prop_id = prop and prop.id or False
            account_id = order.fiscal_position_id.map_account(prop_id)
        if not account_id:
            raise UserError(
                _(
                    'There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') % \
                (self.product_id.name,))

        if self.amount <= 0.00:
            raise UserError(_('The value of the down payment amount must be positive.'))
        if self.advance_payment_method == 'percentage':
            amount = order.amount_total * self.amount / 100
            name = _("Down payment of %s%%") % (self.amount,)
        else:
            amount = self.amount
            name = _('Down Payment')

        invoice = inv_obj.create({
            'name': order.client_order_ref or order.name,
            'origin': order.name,
            'type': 'out_invoice',
            'reference': False,
            'account_id': order.partner_id.property_account_receivable_id.id,
            'partner_id': order.partner_invoice_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': name,
                'origin': order.name,
                'account_id': account_id,
                'price_unit': amount,
                'quantity': 1.0,
                'discount': 0.0,
                'uom_id': self.product_id.uom_id.id,
                'product_id': self.product_id.id,
                'sale_line_ids': [(6, 0, [so_line.id])],
                'invoice_line_tax_ids': [(6, 0, [x.id for x in self.product_id.taxes_id])],
                'account_analytic_id': order.project_id.id or False,
            })],
            'currency_id': order.pricelist_id.currency_id.id,
            'payment_term_id': order.payment_term_id.id,
            'fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
            'team_id': order.team_id.id,
        })
        invoice.compute_taxes()
        return invoice

    @api.multi
    def create_invoices_by_req(self):
        if self.req_id:
            sale_orders = self.req_id.order_ids
        else:
            self.create_invoices()
            return
        invoice = False
        if self.advance_payment_method == 'delivered':
            invoice = sale_orders.action_invoice_create()[0]
        elif self.advance_payment_method == 'all':
            invoice = sale_orders.action_invoice_create(final=True)[0]
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
                    amount = order.amount_total * self.amount / 100
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
                invoice = self._create_invoice(order, so_line, amount).id
        if self.req_id and invoice:
            self.env['requisition.invoice'].browse(self.req_id.id).write({'invoice_id': invoice})
        if self._context.get('open_invoices', False):
            return sale_orders.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}
