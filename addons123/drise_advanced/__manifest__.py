# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Dris 高级版模块',
    'version': '1.0',
    'sequence': 1,
    'summary': '存货成本核算、成本核算、总账',
    'description': """
    """,
    'author': '北京迪威特',
    'website': 'http://www.bjdvt.com',
    'depends': ['base_workflow', 'account', 'hr', 'mrp'],
    'data': [
        'security/ir.model.access.csv',
        'inventory_cost/views/product_view.xml',
        'inventory_cost/views/stock_view.xml',
        'inventory_cost/views/inventory_balance_view.xml',
        'inventory_cost/views/inventory_sequence.xml',
        'inventory_cost/views/inventory_account_view.xml',
        'inventory_cost/views/cost_input_view.xml',
        'inventory_cost/report/transceivers_summary_view.xml',
        'inventory_cost/data/stock_type_data.xml',
        # 'views/account_invoice_view.xml'
        'cost_account/views/cost.xml',
        'cost_account/views/cost_data_fill.xml',
        'cost_account/views/cost_expense.xml',
        'cost_account/views/cost_account_algorithm_view.xml',

        'account_books/wizard/account_report_general_ledger_view.xml',
        'account_books/wizard/account_report_subsidiary_ledger_view.xml',
        'account_books/wizard/account_report_balance_sheet_view.xml',
        'account_books/wizard/account_report_cash_flow_view.xml',
        'account_books/wizard/accounting_set_view.xml',
        'account_books/views/account_view.xml',
        'account_books/views/account_report.xml',
        'account_books/views/report_genrealledger.xml',
        'account_books/views/report_subsidiaryledger.xml',
        'account_books/views/report_balancesheet.xml',
        'account_books/views/report_cashflow.xml',
        'account_books/data/cash_flow_data.xml',
        'account_books/security/ir.model.access.csv',
        'account_move/views/account_move_view.xml',
    ],
    'installable': True,
    'application': True,
}
