# -*- coding: utf-8 -*-

import time
from odoo import api, models
from odoo.exceptions import UserError


class DAReportBalanceSheet(models.AbstractModel):
    _name = 'report.drise_advanced.report_balancesheet'

    def _get_account_move_entry(self, accounts, init_balance, sortby, display_account, groupby, group_choice):
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
        group = {'department': {'groupby': ",l.department_id",
                                'show': "(select department.name from hr_department department where department.id=l.department_id)",
                                'groupid': "coalesce(l.department_id,0)"},
                 'partner': {'groupby': ",l.partner_id",
                             'show': "(select partner.name from res_partner partner where partner.id=l.partner_id)",
                             'groupid': "coalesce(l.partner_id,0)"},
                 'analytics': {'groupby': ",l.analytic_account_id",
                               'show': "(select analytic.name from account_analytic_account analytic where analytic.id=l.analytic_account_id)",
                               'groupid': "coalesce(l.analytic_account_id,0)"},
                 'nothing': {'groupby': "", 'show': "''", "groupid": "0"},
                 'other1': {'groupby': ",l.other_accounting1",
                            'show': "l.other_accounting1",
                            'groupid': "coalesce(l.other_accounting1,0)"},
                 'other2': {'groupby': ",l.other_accounting2",
                            'show': "l.other_accounting2",
                            'groupid': "coalesce(l.other_accounting2,0)"}}
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        if group_choice == 'nothing':
            init_move_lines = dict(map(lambda y: (y, dict(map(lambda x: (x, []), accounts.ids))), groupby['ids']))
            move_lines = dict(map(lambda y: (y, dict(map(lambda x: (x, []), accounts.ids))), groupby['ids']))
        else:
            init_move_lines = dict(map(lambda y: (y, dict(map(lambda x: (x, []), accounts.ids))), groupby.ids))
            init_move_lines[0] = dict(map(lambda x: (x, []), accounts.ids))
            move_lines = dict(map(lambda y: (y, dict(map(lambda x: (x, []), accounts.ids))), groupby.ids))
            move_lines[0] = dict(map(lambda x: (x, []), accounts.ids))

        # Prepare initial sql query and Get the initial move lines
        if init_balance:
            init_tables, init_where_clause, init_where_params = MoveLine.with_context(
                date_from=self.env.context.get('date_from'), date_to=False, initial_bal=True)._query_get()
            init_wheres = [""]
            if init_where_clause.strip():
                init_wheres.append(init_where_clause.strip())
            init_filters = " AND ".join(init_wheres)
            filters = init_filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
            sql = ("""SELECT
      0                                                      AS lid,
      l.account_id                                           AS account_id,
      ''                                                     AS ldate,
      ''                                                     AS lcode,
      NULL                                                   AS amount_currency,
      ''                                                     AS lref,
      'Initial Balance'                                      AS lname,
      COALESCE(SUM(l.debit), 0.0)                            AS debit,
      COALESCE(SUM(l.credit), 0.0)                           AS credit,
      COALESCE(SUM(l.debit), 0) - COALESCE(SUM(l.credit), 0) AS balance,
      ''                                                     AS lpartner_id,
      ''                                                     AS move_name,
      ''                                                     AS mmove_id,
      ''                                                     AS currency_code,
      NULL                                                   AS currency_id,
      ''                                                     AS invoice_id,
      ''                                                     AS invoice_type,
      ''                                                     AS invoice_number,
      ''                                                     AS partner_name, """ +
                   group[group_choice]['show'] + """ AS show_name,""" +
                   group[group_choice]['groupid'] + """ AS groupid""" + """
    FROM account_move_line l
      LEFT JOIN account_move m ON (l.move_id = m.id)
      LEFT JOIN res_currency c ON (l.currency_id = c.id)
      LEFT JOIN res_partner p ON (l.partner_id = p.id)
      LEFT JOIN hr_department dep ON (l.department_id = dep.id)
      LEFT JOIN account_analytic_account ana ON (l.analytic_account_id = ana.id)
      LEFT JOIN account_invoice i ON (m.id = i.move_id)
      JOIN account_journal j ON (l.journal_id = j.id)
    WHERE l.account_id IN %s""" + filters + ' GROUP BY l.account_id' + group[group_choice]['groupby'])
            params = (tuple(accounts.ids),) + tuple(init_where_params)
            cr.execute(sql, params)
            for row in cr.dictfetchall():
                init_move_lines[row['groupid']][row['account_id']].append(row)

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
      p.name                                                 AS partner_name,''' +
               group[group_choice]['show'] + """ AS show_name,""" +
               group[group_choice]['groupid'] + """ AS groupid""" + '''
    FROM account_move_line l
      JOIN account_move M ON (l.move_id = M.id)
      LEFT JOIN res_currency C ON (l.currency_id = C.id)
      LEFT JOIN res_partner p ON (l.partner_id = p.id)
      LEFT JOIN hr_department dep ON (l.department_id = dep.id)
      LEFT JOIN account_analytic_account ana ON (l.analytic_account_id = ana.id)
      JOIN account_journal j ON (l.journal_id = j.id)
      JOIN account_account acc ON (l.account_id = acc.id)
    WHERE l.account_id IN %s''' + filters + '''
    GROUP BY l.id, l.account_id, l.date, j.code, l.currency_id, l.amount_currency, l.ref, l.name, m.name, c.symbol, p.name'''
               + group[group_choice]['groupby'] + ''' ORDER BY ''' + sql_sort)
        params = (tuple(accounts.ids),) + tuple(where_params)
        cr.execute(sql, params)

        for row in cr.dictfetchall():
            balance = init_move_lines[row['groupid']][row['account_id']][0]['balance'] if init_move_lines.get(
                row['groupid']) and init_move_lines.get(row['groupid']).get(row['account_id']) else 0
            for line in move_lines.get(row['groupid']).get(row['account_id']):
                balance += line['debit'] - line['credit']
            row['balance'] += balance
            move_lines[row['groupid']][row['account_id']].append(row)

        # Calculate the debit, credit and balance for Accounts
        group_res = []
        if group_choice == 'nothing':
            account_res = []
            for account in accounts:
                if account.id == 104:
                    pass
                currency = account.currency_id and account.currency_id or account.company_id.currency_id
                res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
                res['code'] = account.code
                res['name'] = account.name
                if account.balance_direct == 'credit':
                    direct = -1
                else:
                    direct = 1
                # 期初
                if init_move_lines.get(0) and init_move_lines.get(0).get(account.id):
                    res['init_balance'] = init_move_lines[0][account.id][0]['balance'] * direct
                    res['init_debit'] = init_move_lines[0][account.id][0]['debit']
                    res['init_credit'] = init_move_lines[0][account.id][0]['credit']
                else:
                    res['init_balance'] = 0.0
                    res['init_debit'] = 0.0
                    res['init_credit'] = 0.0
                # 期末
                res['debit'] = res['init_debit']
                res['credit'] = res['init_credit']
                res['move_lines'] = move_lines[0][account.id]
                for line in res.get('move_lines'):
                    res['debit'] += line['debit']
                    res['credit'] += line['credit']
                res['balance'] = (res['debit'] - res['credit']) * direct
                # 发生
                res['ing_debit'] = res['debit'] - res['init_debit']
                res['ing_credit'] = res['credit'] - res['init_credit']
                res['ing_balance'] = (res['ing_debit'] - res['ing_credit']) * direct
                if display_account in ('all', 'just'):
                    account_res.append(res)
                if display_account == 'movement' and res.get('move_lines'):
                    account_res.append(res)
                if display_account == 'not_zero' and not currency.is_zero(res['balance']):
                    account_res.append(res)
            if display_account in ('all', 'just'):
                group_res.append({"account": account_res, "name": False})
            elif display_account in ('movement', 'not_zero') and account_res:
                group_res.append({"account": account_res, "name": False})
        else:
            for source_group in groupby:
                account_res = []
                for account in accounts:
                    currency = account.currency_id and account.currency_id or account.company_id.currency_id
                    res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
                    res['code'] = account.code
                    res['name'] = account.name
                    if account.balance_direct == 'credit':
                        direct = -1
                    else:
                        direct = 1
                    # 期初
                    if init_move_lines.get(source_group.id) and init_move_lines.get(source_group.id).get(account.id):
                        res['init_balance'] = init_move_lines[source_group.id][account.id][0]['balance'] * direct
                        res['init_debit'] = init_move_lines[source_group.id][account.id][0]['debit']
                        res['init_credit'] = init_move_lines[source_group.id][account.id][0]['credit']
                    else:
                        res['init_balance'] = 0.0
                        res['init_debit'] = 0.0
                        res['init_credit'] = 0.0
                    # 期末
                    res['move_lines'] = move_lines[source_group.id][account.id]
                    res['debit'] = res['init_debit']
                    res['credit'] = res['init_credit']
                    for line in res.get('move_lines'):
                        res['debit'] += line['debit']
                        res['credit'] += line['credit']
                    res['balance'] = (res['debit'] - res['credit']) * direct
                    # 发生
                    res['ing_debit'] = res['debit'] - res['init_debit']
                    res['ing_credit'] = res['credit'] - res['init_credit']
                    res['ing_balance'] = (res['ing_debit'] - res['ing_credit']) * direct
                    if display_account in ('all', 'just'):
                        account_res.append(res)
                    if display_account == 'movement' and res.get('move_lines'):
                        account_res.append(res)
                    if display_account == 'not_zero' and not currency.is_zero(res['balance']):
                        account_res.append(res)
                if display_account in ('all', 'just'):
                    group_res.append({"account": account_res, "name": source_group.name})
                elif display_account in ('movement', 'not_zero') and account_res:
                    group_res.append({"account": account_res, "name": source_group.name})

        return group_res

    @api.model
    def render_html(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))

        init_balance = data['form'].get('initial_balance', True)
        sortby = data['form'].get('sortby', 'sort_date')
        display_account = data['form']['display_account']
        codes = []
        if data['form'].get('journal_ids', False):
            codes = [journal.code for journal in
                     self.env['account.journal'].search([('id', 'in', data['form']['journal_ids'])])]
        domain = []
        if display_account == 'just':
            domain.append(('id', '=', data['form']['account_chosen']))
            data['form']['account_chosen'] = self.env['account.account'].browse(data['form']['account_chosen']).name
        if data['mode'] == 'department':
            domain.append(('department_accounting', '=', True))
            groupby = self.env['hr.department'].search([])
        elif data['mode'] == 'partner':
            domain.append(('partner_accounting', '=', True))
            groupby = self.env['res.partner'].search([('partner_share', '=', True)])
        elif data['mode'] == 'analytics':
            domain.append(('analytic_accounting', '=', True))
            groupby = self.env['account.analytic.account'].search([])
        elif data['mode'] == 'other1':
            domain.append(('other_accounting1', '=', True))
            groupby = self.env["account.other.accounting1"].search([])
        elif data['mode'] == 'other2':
            domain.append(('other_accounting2', '=', True))
            groupby = self.env["account.other.accounting2"].search([])
        else:
            groupby = {'ids': [0], 'name': False}
        accounts = docs if self.model == 'account.account' else self.env['account.account'].search(domain)
        if not accounts:
            raise UserError(_("没有以此方式核算的科目"))
        accounts_res = self.with_context(data['form'].get('used_context', {}))._get_account_move_entry(accounts,
                                                                                                       init_balance,
                                                                                                       sortby,
                                                                                                       display_account,
                                                                                                       groupby,
                                                                                                       data['mode'])
        docargs = {
            'doc_ids': docids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'Accounts': accounts_res,
            'print_journal': codes,
        }
        return self.env['report'].render('drise_advanced.report_balancesheet', docargs)
