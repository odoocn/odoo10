# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DAAccountReportSubsidiaryLedger(models.TransientModel):
    _inherit = "account.common.account.report"
    _name = "account.report.subsidiary.ledger"
    _description = "Subsidiary Ledger Report"

    initial_balance = fields.Boolean(string='包含期初金额', default=True)
    sortby = fields.Selection([('sort_date', '日期'), ('sort_journal_partner', '日记账 & 业务伙伴')], string='排序',
                              required=True, default='sort_date')
    journal_ids = fields.Many2many('account.journal', 'account_report_subsidiary_ledger_journal_rel', 'account_id',
                                   'journal_id', string='日记账', required=True)

    accounting_mode = fields.Selection([('nothing', u'无'),
                                        ('partner', u'业务伙伴'),
                                        ('department', u'部门'),
                                        ('analytics', u'分析账户')], string=u'核算方式',
                                       required=True, default='nothing')

    display_account = fields.Selection(selection_add=[('just', u'指定科目')])
    account_chosen = fields.Many2one('account.account', string=u'科目')
    date_from = fields.Date(string='开始时间', required=True)

    @api.onchange('accounting_mode')
    def onchange_mode(self):
        if self.accounting_mode == 'partner':
            return {'domain': {"account_chosen": [('partner_accounting', '=', True)]}}
        if self.accounting_mode == 'department':
            return {'domain': {"account_chosen": [('department_accounting', '=', True)]}}
        if self.accounting_mode == 'analytics':
            return {'domain': {"account_chosen": [('analytic_accounting', '=', True)]}}
        if self.accounting_mode == 'other1':
            return {'domain': {"account_chosen": [('other_accounting1', '=', True)]}}
        if self.accounting_mode == 'other2':
            return {'domain': {"account_chosen": [('other_accounting2', '=', True)]}}
        return {'domain': {"account_chosen": []}}

    def _print_report(self, data):
        data = self.pre_print_report(data)
        data['mode'] = self.read(['accounting_mode'])[0]['accounting_mode']
        data['account_chosen'] = self.read(['account_chosen'])[0]['account_chosen']
        if self.read(['account_chosen'])[0]['account_chosen']:
            data['form']['account_chosen'] = self.read(['account_chosen'])[0]['account_chosen'][0]
        data['form'].update(self.read(['initial_balance', 'sortby'])[0])
        if data['form'].get('initial_balance') and not data['form'].get('date_from'):
            raise UserError(_("你必须确定开始时间"))
        records = self.env[data['model']].browse(data.get('ids', []))

        domain = []
        if self.display_account == 'just':
            domain.append(('id', '=', data['form']['account_chosen']))
        if data['mode'] == 'department':
            domain.append(('department_accounting', '=', True))
        elif data['mode'] == 'partner':
            domain.append(('partner_accounting', '=', True))
        elif data['mode'] == 'analytics':
            domain.append(('analytic_accounting', '=', True))
        elif data['mode'] == 'other1':
            domain.append(('other_accounting1', '=', True))
        elif data['mode'] == 'other2':
            domain.append(('other_accounting2', '=', True))
        accounts = records if data['model'] == 'account.account' else self.env['account.account'].search(domain)
        if not accounts:
            raise UserError(_("没有以此方式核算的科目"))

        return self.env['report'].with_context(landscape=True).get_action(records,
                                                                          'drise_advanced.report_subsidiaryledger',
                                                                          data=data)
