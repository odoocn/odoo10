# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DAAccountReportGeneralLedger(models.TransientModel):
    _inherit = "account.report.general.ledger"

    accounting_mode = fields.Selection([('nothing', u'无'),
                                        ('partner', u'业务伙伴'),
                                        ('department', u'部门'),
                                        ('analytics', u'分析账户'),
                                        ('other1', u'扩展辅助核算1'),
                                        ('other2', u'扩展辅助核算2')], string=u'辅助核算',
                                       required=True, default='nothing')

    display_account = fields.Selection(selection_add=[('just', u'指定科目')])
    account_chosen = fields.Many2one('account.account', string=u'科目')
    initial_balance = fields.Boolean(default=True)
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
        data['mode'] = self.read(['accounting_mode'])[0]['accounting_mode']
        data['account_chosen'] = self.read(['account_chosen'])[0]['account_chosen']
        if self.read(['account_chosen'])[0]['account_chosen']:
            data['form']['account_chosen'] = self.read(['account_chosen'])[0]['account_chosen'][0]
        data = self.pre_print_report(data)
        data['form'].update(self.read(['initial_balance', 'sortby'])[0])
        if data['form'].get('initial_balance') and not data['form'].get('date_from'):
            raise UserError(_("You must define a Start Date"))
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

        return self.env['report'].with_context(landscape=True).get_action(records, 'account.report_generalledger', data=data)
