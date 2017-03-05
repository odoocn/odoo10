#coding:utf-8
from odoo import tools, api, models, fields

class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    purchase_num=fields.Char(compute='purchase_count')
    purchase_invoice_order_num=fields.Char(compute='purchase_invoice_order_count')
    sale_invoice_order_num=fields.Char(compute='sale_invoice_order_count')
    sale_order_num=fields.Char(compute='sale_order_count')

    @api.one
    def sale_order_count(self):

        sales=self.env['sale.order'].search([])
        a=[]
        for sale in sales:
            if sale.project_id.id == self.id:
                if sale.id not in a:
                    a.append(sale.id)
        for obj in self:
            obj.sale_order_num=len(a)
    @api.one
    def sale_invoice_order_count(self):
        requisitions=self.env['requisition.invoice'].search([])
        a=[]
        for requisition in requisitions:
            for sale in requisition.order_ids:
                if sale.project_id.id == self.id:
                    if requisition.id not in a:
                        a.append(requisition.id)
        for obj in self:
            obj.sale_invoice_order_num=len(a)
    @api.one
    def purchase_invoice_order_count(self):
        requisitions=self.env['requisition.pay'].search([])
        order_line = self.env['purchase.order.line'].search(
            [('account_analytic_id', '=', self.id), ('order_id.state', 'in', ('purchase', 'done'))])
        purchase_order_ids = []
        for line in order_line:
            if line.order_id.id not in purchase_order_ids:
                purchase_order_ids.append(line.order_id.id)
        a=[]
        for requisition in requisitions:
            for purchase in requisition.purchase_ids:
                if purchase.id in purchase_order_ids:
                        if requisition.id not in a:
                            a.append(requisition.id)
        for obj in self:
            obj.purchase_invoice_order_num=len(a)
    @api.one
    def purchase_count(self):
        order_line = self.env['purchase.order.line'].search(
            [('account_analytic_id', '=', self.id), ('order_id.state', 'in', ('purchase', 'done'))])
        purchase_order_ids = []
        for line in order_line:
            if line.order_id.id not in purchase_order_ids:
                purchase_order_ids.append(line.order_id.id)

        for obj in self:
            obj.purchase_num=len(purchase_order_ids)

    @api.multi
    def find_purchase_order(self):
        order_line = self.env['purchase.order.line'].search(
            [('account_analytic_id', '=', self.id), ('order_id.state', 'in', ('purchase', 'done'))])
        purchase_order_ids = []
        for line in order_line:
            if line.order_id.id not in purchase_order_ids:
                purchase_order_ids.append(line.order_id.id)
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('purchase.purchase_form_action')
        list_view_id = imd.xmlid_to_res_id('purchase.purchase_order_tree')
        form_view_id = imd.xmlid_to_res_id('purchase.purchase_order_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(purchase_order_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % purchase_order_ids
        elif len(purchase_order_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = purchase_order_ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    @api.multi
    def find_purchase_invoice_order(self):
        requisitions=self.env['requisition.pay'].search([])
        order_line = self.env['purchase.order.line'].search(
            [('account_analytic_id', '=', self.id), ('order_id.state', 'in', ('purchase', 'done'))])
        purchase_order_ids = []
        for line in order_line:
            if line.order_id.id not in purchase_order_ids:
                purchase_order_ids.append(line.order_id.id)
        a=[]
        for requisition in requisitions:
            for purchase in requisition.purchase_ids:
                if purchase.id in purchase_order_ids:
                        if requisition.id not in a:
                            a.append(requisition.id)
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('driserp_requisition.action_requisition_all')
        list_view_id = imd.xmlid_to_res_id('driserp_requisition.requisition_pay_view_tree')
        form_view_id = imd.xmlid_to_res_id('driserp_requisition.requisition_pay_watch_view')
        result = {
            'name': action.name,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(a) > 1:
            result['domain'] = "[('id','in',%s)]" % a
        elif len(a) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = a[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    @api.multi
    def find_sale_invoice_order(self):
        requisitions=self.env['requisition.invoice'].search([])
        a=[]
        for requisition in requisitions:
            for sale in requisition.order_ids:
                if sale.project_id.id == self.id:
                    if requisition.id not in a:
                        a.append(requisition.id)
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('driserp_requisition.action_requisition_invoice_all')
        list_view_id = imd.xmlid_to_res_id('driserp_requisition.requisition_invoice_view_tree')
        form_view_id = imd.xmlid_to_res_id('driserp_requisition.requisition_invoice_watch_view')
        result = {
            'name': action.name,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(a) > 1:
            result['domain'] = "[('id','in',%s)]" % a
        elif len(a) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = a[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    @api.multi
    def find_sale_order(self):
        sales=self.env['sale.order'].search([])
        a=[]
        for sale in sales:
            if sale.project_id.id == self.id:
                if sale.id not in a:
                    a.append(sale.id)

        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('sale.action_orders')
        list_view_id = imd.xmlid_to_res_id('sale.view_order_tree')
        form_view_id = imd.xmlid_to_res_id('sale.view_order_form')
        result = {
            'name': action.name,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(a) > 1:
            result['domain'] = "[('id','in',%s)]" % a
        elif len(a) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = a[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
