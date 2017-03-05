# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools, api, models, fields


class analytic_report(models.Model):
    _name = "analytic.report"
    _description = "Analytic Statistics"
    _auto = False
    _rec_name = 'lead_id'

    lead_id = fields.Many2one('account.analytic.account', string=u'分析账户', readonly=True)
    opportunity = fields.Many2one('crm.lead', string=u'商机', readonly=True)
    partner_id = fields.Many2one('res.partner', string=u'客户', readonly=True)
    user_id = fields.Many2one('res.users', string=u'销售员', readonly=True)
    sale_amount = fields.Float('销售总额', readonly=True)
    purchase_amount = fields.Float('采购总额', readonly=True)
    expense_amount = fields.Float('费用', readonly=True)
    invoice_amount = fields.Float('客户开票', readonly=True)
    invoice_pay = fields.Float('收款总额', readonly=True)

    _order = 'lead_id desc'

    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
CREATE or REPLACE VIEW public.analytic_report AS
SELECT
  a.id                                                                                                  AS id,
  a.id                                                                                                  AS lead_id,
  crm.id                                                                                                AS opportunity,
  crm.partner_id                                                                                        AS partner_id,
  crm.user_id                                                                                           AS user_id,
  (SELECT sum(sale.amount_total)
   FROM sale_order sale
   WHERE sale.project_id = a.id AND sale.state IN ('sale', 'done'))                                     AS sale_amount,
  (SELECT sum(purchase.price_total)
   FROM purchase_order_line purchase LEFT JOIN purchase_order p ON p.id = purchase.order_id
   WHERE purchase.account_analytic_id = a.id AND p.state IN
                                                 ('purchase', 'done'))                                  AS purchase_amount,
  (SELECT sum(ex.total_amount)
   FROM hr_expense ex
   LEFT JOIN hr_expense_sheet sheet ON sheet.id=ex.sheet_id
   WHERE sheet.state IN ('approve', 'post', 'done') AND ex.analytic_account_id =
                                              a.id)                                                     AS expense_amount,
  (SELECT sum(invoice.price_unit * invoice.quantity)
   FROM account_invoice_line invoice LEFT JOIN account_invoice i ON invoice.invoice_id = i.id
   WHERE i.state IN ('paid', 'open') AND i.type = 'out_invoice' AND invoice.account_analytic_id =
                                                                    a.id)                               AS invoice_amount,
  (SELECT coalesce(sum(i.residual), 0)
   FROM account_invoice_line invoice LEFT JOIN account_invoice i ON invoice.invoice_id = i.id
   WHERE i.state IN ('paid', 'open') AND i.type = 'out_invoice' AND invoice.account_analytic_id =
                                                                    a.id)                               AS invoice_pay
FROM account_analytic_account a
  LEFT JOIN crm_lead crm ON crm.account_analytic_id = a.id;""")

    @api.multi
    def sale_search(self):
        sale_order = self.env['sale.order'].search([('project_id', '=', self.lead_id.id), ('state', 'in', ('sale', 'done'))])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('sale.action_orders')
        list_view_id = imd.xmlid_to_res_id('sale.view_quotation_tree')
        form_view_id = imd.xmlid_to_res_id('sale.view_order_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(sale_order) > 1:
            result['domain'] = "[('id','in',%s)]" % sale_order.ids
        elif len(sale_order) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = sale_order.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    @api.multi
    def purchase_search(self):
        order_line = self.env['purchase.order.line'].search(
            [('account_analytic_id', '=', self.lead_id.id), ('order_id.state', 'in', ('purchase', 'done'))])
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
    def expense_search(self):
        order_line = self.env['hr.lines'].search(
            [('analytic_account_id', '=', self.lead_id.id), ('expense_id.state', 'in', ('approve', 'post', 'done'))])
        expense_ids = []
        for line in order_line:
            if line.expense_id.id not in expense_ids:
                expense_ids.append(line.expense_id.id)
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('hr_expense.action_approved_expense')
        list_view_id = imd.xmlid_to_res_id('hr_expense.view_expenses_tree')
        form_view_id = imd.xmlid_to_res_id('hr_expense.hr_expense_form_view')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(expense_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % expense_ids
        elif len(expense_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = expense_ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    @api.multi
    def invoice_search(self):
        order_line = self.env['account.invoice.line'].search(
            [('account_analytic_id', '=', self.lead_id.id), ('invoice_id.state', 'in', ('open', 'paid'))])
        invoice_ids = []
        for line in order_line:
            if line.invoice_id.id not in invoice_ids:
                invoice_ids.append(line.invoice_id.id)
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_invoice_tree')
        list_view_id = imd.xmlid_to_res_id('account.invoice_tree')
        form_view_id = imd.xmlid_to_res_id('account.invoice_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(invoice_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % invoice_ids
        elif len(invoice_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = invoice_ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    @api.multi
    def payment_search(self):
        sale_order = self.env['sale.order'].search([('project_id', '=', self.lead_id.id)])
        payment_ids = self.env['account.payment'].search([('sale_id', 'in', sale_order.ids)]).ids

        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_account_payments')
        list_view_id = imd.xmlid_to_res_id('account.view_account_payment_tree')
        form_view_id = imd.xmlid_to_res_id('account.view_account_payment_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(payment_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % payment_ids
        elif len(payment_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = payment_ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result


class analytic_single_report(models.Model):
    _name = "analytic.single.report"
    _description = "Analytic Single Statistics"
    _auto = False
    _rec_name = 'line_type'

    amount = fields.Float('总额', readonly=True)
    partner_name = fields.Char(u'业务对象')
    line_type = fields.Selection([('sale', '销售'),
                                  ('purchase', '采购'),
                                  ('invoice', '客户发票'),
                                  ('bills', '供应商帐单'),
                                  ('in_pay', '收款'),
                                  ('out_pay', '付款'),
                                  ('expense', '费用')], string='类型', readonly=True)
    line_date = fields.Date(u'发生时间', readonly=True)
    product = fields.Many2one('product.product', u'产品', readonly=True)
    qty = fields.Float(u'数量', readonly=True)
    re_name = fields.Char(u'名称')

    _order = 'line_date desc'

    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
CREATE or REPLACE VIEW public.analytic_single_report AS
SELECT id,partner_name,SUM(amount) as amount,line_type, line_date, product, sum(qty) as qty, re_name FROM
(
  SELECT
    s.id AS id,
    sale_partner.name as partner_name,
    s.product_id as product,
    s.product_uom_qty as qty,
    s.price_total AS amount,
    'sale'           AS line_type,
    sale.data_from  AS line_date,
    sale.order_name AS re_name
  FROM sale_order_line s LEFT JOIN sale_order sale on sale.id=s.order_id
    LEFT JOIN res_partner sale_partner on sale_partner.id=sale.partner_id
  WHERE sale.state IN ('sale', 'done')
  UNION
  SELECT
    p.id+100000000 AS id,
    pur_partner.name as partner_name,
    p.product_id as product,
    p.product_qty as qty,
    p.price_total AS amount,
    'purchase' AS line_type,
    po.data_from AS line_date,
    po.order_name as re_name
  FROM purchase_order_line p LEFT JOIN purchase_order po on po.id=p.order_id
    LEFT JOIN res_partner pur_partner ON pur_partner.id=po.partner_id
  WHERE po.state IN ('purchase', 'done')
  UNION
  SELECT
    i.id+200000000 AS id,
    inv_partner.name as partner_name,
    i.product_id as product,
    i.quantity as qty,
    i.price_unit*i.quantity AS amount,
    'invoice'      AS line_type,
    invoice.date_invoice  AS line_date,
    inv_order.order_name AS re_name
  FROM account_invoice_line i LEFT JOIN account_invoice invoice on invoice.id=i.invoice_id
    LEFT JOIN res_partner inv_partner ON inv_partner.id=invoice.partner_id
    LEFT JOIN sale_order_line_invoice_rel inv_ref ON inv_ref.invoice_line_id=i.id
    LEFT JOIN sale_order_line inv_line on inv_ref.order_line_id=inv_line.id
    LEFT JOIN sale_order inv_order on inv_order.id=inv_line.order_id
  WHERE invoice.state IN ('open', 'paid') AND invoice.type = 'out_invoice'
  UNION
  SELECT
    o.id+300000000 AS id,
    bil_partner.name as partner_name,
    o.product_id as product,
    o.quantity as qty,
    o.price_unit*o.quantity AS amount,
    'bills'      AS line_type,
    bills.date_invoice  AS line_date,
    bil_po.order_name as re_name
  FROM account_invoice_line o LEFT JOIN account_invoice bills on bills.id=o.invoice_id
    LEFT JOIN res_partner bil_partner ON bil_partner.id=bills.partner_id
    LEFT JOIN purchase_order_line bil_po_line on bil_po_line.id=o.purchase_line_id
    LEFT JOIN purchase_order bil_po on bil_po.id=bil_po_line.order_id
  WHERE bills.state IN ('open', 'paid') AND bills.type = 'in_invoice'
  UNION
  SELECT
    ip.id+400000000 AS id,
    pay_partner.name AS partner_name,
    NULL AS product,
    1 as qty,
    ip.amount as amount,
    'out_pay' as line_type,
    ip.payment_date as line_date,
    NULL as re_name
  FROM account_payment ip LEFT JOIN res_partner pay_partner ON pay_partner.id=ip.partner_id
  WHERE ip.state<>'draft' and ip.payment_type='outbound'
  UNION
  SELECT
    op.id+500000000 AS id,
    in_partner.name AS partner_name,
    NULL AS product,
    1 as qty,
    op.amount as amount,
    'in_pay' as line_type,
    op.payment_date as line_date,
    NULL AS re_name
  FROM account_payment op LEFT JOIN res_partner in_partner ON in_partner.id=op.partner_id
  WHERE op.state<>'draft' and op.payment_type='inbound'
  UNION
  SELECT
    ex.id+600000000 AS id,
    ex_hr.name_related as partner_name,
    ex.product_id AS product,
    ex.quantity as qty,
    ex.total_amount as amount,
    'expense' as line_type,
    ex_sheet.expense_date as line_date,
    ex.name as re_name
  FROM hr_expense ex
    LEFT JOIN hr_employee ex_hr ON ex_hr.id=ex.employee_id
    LEFT JOIN hr_expense_sheet ex_sheet on ex_sheet.id=ex.sheet_id
  WHERE ex_sheet.state in ('approve', 'post', 'done')
)  AAA
  GROUP BY id,line_type,line_date,product,qty,partner_name,re_name ORDER BY line_date;""")


class analytic_sale(models.Model):
    _name = "analytic.sale"
    _description = "Analytic Sale Order"
    _auto = False
    _rec_name = 'order_id'

    @api.depends('order_id')
    def _compute_payment_amount(self):
        for r in self:
            r.payment_amount = r.order_id.order_paid

    order_id = fields.Many2one('sale.order', string=u'销售订单')
    order_name = fields.Char(string=u'订单名称')
    order_date = fields.Date(string=u'单据日期')
    amount = fields.Float(u'销售金额', readonly=True)
    partner_id = fields.Many2one('res.partner', string=u'客户')
    invoice_amount = fields.Float(string=u'开票金额', readonly=True)
    payment_amount = fields.Float(string=u'收款', readonly=True, compute=_compute_payment_amount)

    _order = 'order_id desc'

    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
    CREATE or REPLACE VIEW public.analytic_sale AS
    SELECT
  sale.id as id,
  sale.id as order_id,
  sale.order_name as order_name,
  sale.data_from as order_date,
  sale.partner_id as partner_id,
  sum(sale.amount_total) as amount,
  (SELECT sum(invoice_line.quantity*invoice_line.price_unit) as amount FROM sale_order_line_invoice_rel rel
    LEFT JOIN sale_order_line sale_line on sale_line.id=rel.order_line_id
    LEFT JOIN sale_order sorder on sorder.id=sale_line.order_id
    LEFT JOIN account_invoice_line invoice_line on invoice_line.id=rel.invoice_line_id
    LEFT JOIN account_invoice invoice on invoice.id=invoice_line.invoice_id
      WHERE sorder.id=sale.id and invoice.state in ('paid', 'open')) as invoice_amount
FROM sale_order sale GROUP BY sale.id;""")

    @api.multi
    def view_sale(self):
        sale_id = self.order_id.id
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('sale.action_orders')
        form_view_id = imd.xmlid_to_res_id('sale.view_order_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            'res_id': sale_id
        }
        return result


class analytic_purchase(models.Model):
    _name = "analytic.purchase"
    _description = "Analytic Purchase Order"
    _auto = False
    _rec_name = 'order_id'

    @api.depends('order_id')
    def _compute_payment_amount(self):
        for r in self:
            r.payment_amount = r.order_id.order_paid

    order_id = fields.Many2one('purchase.order', string=u'采购订单')
    amount = fields.Float(u'采购金额', readonly=True)
    partner_id = fields.Many2one('res.partner', string=u'供应商')
    bills_amount = fields.Float(string=u'账单金额', readonly=True)
    payment_amount = fields.Float(string=u'付款', readonly=True, compute=_compute_payment_amount)
    order_name = fields.Char(string=u'订单名称')
    order_date = fields.Date(string=u'单据日期')

    _order = 'order_id desc'

    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
    CREATE or REPLACE VIEW public.analytic_purchase AS
    SELECT
  purchase.id as id,
  purchase.id as order_id,
  purchase.amount_total as amount,
  purchase.order_name as order_name,
  purchase.data_from as order_date,
  purchase.partner_id as partner_id,
  (SELECT sum(line.price_unit*line.quantity) FROM account_invoice_line line
  LEFT JOIN account_invoice bills on bills.id=line.invoice_id
  LEFT JOIN purchase_order_line p_line on line.purchase_line_id=p_line.id
  WHERE p_line.order_id=purchase.id and bills.state in ('paid', 'open')) as bills_amount
FROM purchase_order purchase GROUP BY purchase.id;""")

    @api.multi
    def view_purchase(self):
        purchase_id = self.order_id.id
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('purchase.purchase_form_action')
        form_view_id = imd.xmlid_to_res_id('purchase.purchase_order_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            'res_id': purchase_id
        }
        return result
