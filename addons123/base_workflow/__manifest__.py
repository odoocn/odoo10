# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': '基础 工作流配置',
    'version': '1.0',
    'sequence': 1,
    'summary': '工作流配置',
    'description': """
    """,
    'author': '北京迪威特',
    'website': 'http://www.bjdvt.com',
    'depends': ['hr', 'base', 'purchase', 'sale', 'hr_expense', 'driserp_requisition', 'crm', 'account_cancel', 'analytic',
                'vnsoft_form_hide_edit'],

    'data': [
        'views/workflow_view.xml',
        'views/workflow_history_view.xml',
        'views/workflow_requisition_view.xml',
        'views/workflow_req_invoice_view.xml',
        'views/workflow_purchase_view.xml',
        'views/workflow_sale_view.xml',
        'views/workflow_hr_expense_view.xml',
        'views/purchase_sale_type_view.xml',
        'views/type_account_relation_view.xml',
        'report/analytic_report_view.xml',
        'stable/views/stable_analytic_add.xml',
        'stable/views/add_code.xml',
        'security/ir.model.access.csv',
        'data/stock_type_data.xml',
        'views/workflow_report.xml',
        'stable/views/line_no.xml',
        'static/report/report_stockpicking_operations.xml',
        'stable/views/stock_view.xml',
        'stable/views/product_view.xml',
    ],
    'installable': True,
    'application': True,
}
