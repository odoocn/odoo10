# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'DRISERP-Requisition',
    'version': '1.0',
    'sequence': 2,
    'summary': '申请',
    'description': """
    """,
    'author': '北京迪威特',
    'website': 'http://www.bjdvt.com',
    'depends': ['account', 'payment', 'sale', 'purchase'],
    'data': [
        'views/account_invoice_view.xml',
        'views/requisition_view.xml',
        'views/sale_view.xml',
        'views/purchase_view.xml',
        'security/ir.model.access.csv',
        'security/requisition_security.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
}
