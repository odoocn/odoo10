# -*- coding: utf-8 -*-

import time
from odoo import api, models


class DAReportCashFlow(models.AbstractModel):
    _name = 'report.drise_advanced.report_cashflow'

    def _get_account_move_entry(self, accounts, sortby, cash_flow):
        """
        :param:
                accounts: the recordset of accounts
                init_balance: boolean value of initial_balance
                sortby: sorting by date or partner and journal
                display_account: type of account(receivable, payable and both)

        Returns a dictionary of accounts with following key and value {
                'code': account code,
                'name': account name,
                'debit': sum of total debit amount,
                'credit': sum of total credit amount,
                'balance': total balance,
                'amount_currency': sum of amount_currency,
                'move_lines': list of move line
        }
        """
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        move_lines = dict(map(lambda x: (x, []), cash_flow.ids))
        move_lines[0] = []

        sql_sort = 'l.date, l.move_id'
        if sortby == 'sort_journal_partner':
            sql_sort = 'j.code, p.name, l.move_id'

        # Prepare sql query base on selected parameters from wizard
        tables, where_clause, where_params = MoveLine._query_get()
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        filters = filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')

        # Get move lines base on sql query and Calculate the total balance of move lines
        sql = ('''SELECT
  l.id                                                   AS lid,
  l.account_id                                           AS account_id,
  l.date                                                 AS ldate,
  j.code                                                 AS lcode,
  l.currency_id,
  l.amount_currency,
  l.ref                                                  AS lref,
  l.name                                                 AS lname,
  COALESCE(l.debit, 0)                                   AS debit,
  COALESCE(l.credit, 0)                                  AS credit,
  COALESCE(SUM(l.debit), 0) - COALESCE(SUM(l.credit), 0) AS balance,
  M.name                                                 AS move_name,
  C.symbol                                               AS currency_code,
  p.name                                                 AS partner_name,
  COALESCE(l.cash_flow_item, 0)                          AS cash_flow_item
FROM account_move_line l
  JOIN account_move M ON (l.move_id = M.id)
  LEFT JOIN res_currency C ON (l.currency_id = C.id)
  LEFT JOIN res_partner p ON (l.partner_id = p.id)
  JOIN account_journal j ON (l.journal_id = j.id)
  JOIN account_account acc ON (l.account_id = acc.id)
WHERE l.account_id IN %s ''' + filters + '''
GROUP BY l.id, l.date, j.code, l.currency_id, l.amount_currency, l.ref, l.name, m.name, c.symbol, p.name, l.cash_flow_item
ORDER BY ''' + sql_sort)
        params = (tuple(accounts.ids),) + tuple(where_params)
        cr.execute(sql, params)

        for row in cr.dictfetchall():
            balance = 0
            for line in move_lines.get(row['cash_flow_item']):
                balance += line['debit'] - line['credit']
            row['balance'] += balance
            move_lines[row['cash_flow_item']].append(row)

        cash_flow_res = []
        for flow in cash_flow:
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            res['name'] = flow.name
            res['move_lines'] = move_lines[flow.id]
            for line in res.get('move_lines'):
                res['debit'] += line['debit']
                res['credit'] += line['credit']
                res['balance'] = line['balance']
            if res['move_lines']:
                cash_flow_res.append(res)
        # 处理未指定项目分录
        res_0 = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
        res_0['name'] = u'未指定现金流量项目'
        res_0['move_lines'] = move_lines[0]
        for line in res_0.get('move_lines'):
            res_0['debit'] += line['debit']
            res_0['credit'] += line['credit']
            res_0['balance'] = line['balance']
        if res_0['move_lines']:
            cash_flow_res.append(res_0)

        return cash_flow_res

    @api.model
    def render_html(self, docids, data=None):
        cash_type_ids = self.env['account.account.type'].search([('type', '=', 'liquidity')]).ids
        cash_flow = self.env['account.cash.flow'].search([])
        accounts = self.env['account.account'].search([("user_type_id", "in", cash_type_ids)])
        sortby = data['form'].get('sortby', 'sort_date')
        codes = []
        if data['form'].get('journal_ids', False):
            codes = [journal.code for journal in self.env['account.journal'].search([('id', 'in', data['form']['journal_ids'])])]

        accounts_res = self.with_context(data['form'].get('used_context',{}))._get_account_move_entry(accounts, sortby,
                                                                                                      cash_flow)
        docargs = {
            'doc_ids': docids,
            'doc_model': self.env.context.get('active_model'),
            'data': data['form'],
            'docs': accounts,
            'time': time,
            'Accounts': accounts_res,
            'print_journal': codes,
        }
        return self.env['report'].render('drise_advanced.report_cashflow', docargs)
