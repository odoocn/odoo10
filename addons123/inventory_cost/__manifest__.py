# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': '基础 存货成本核算',
    'version': '1.0',
    'sequence': 1,
    'summary': '存货成本核算',
    'description': """
    """,
    'author': '北京迪威特',
    'website': 'http://www.bjdvt.com',
    'depends': ['product', 'stock', 'purchase', 'sale', 'account', 'base_workflow'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_view.xml',
        'views/stock_view.xml',
        'views/inventory_balance_view.xml',
        'views/inventory_sequence.xml',
        'views/inventory_account_view.xml',
        'report/transceivers_summary_view.xml',
        # 'stock_type_data.xml',
        # 'views/account_invoice_view.xml'
    ],
    'installable': True,
    'application': True,
}
