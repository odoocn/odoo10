# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DACashFlow(models.TransientModel):
    _inherit = "account.common.report"
    _name = "account.report.cash.flow"
    _description = "Cash Flow Report"

    sortby = fields.Selection([('sort_date', '日期'), ('sort_journal_partner', '日记账 & 业务伙伴')], string='排序',
                              required=True, default='sort_date')
    journal_ids = fields.Many2many('account.journal', 'account_report_cash_flow_journal_rel', 'account_id',
                                   'journal_id', string='日记账', required=True)
    date_from = fields.Date(string='开始时间', required=True)

    def _print_report(self, data):
        data['form'].update(self.read(['sortby'])[0])
        records = self.env[data['model']].browse(data.get('ids', []))
        return self.env['report'].with_context(landscape=True).get_action(records,
                                                                          'drise_advanced.report_cashflow',
                                                                          data=data)
