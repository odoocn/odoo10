# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': '基础 PLUS',
    'version': '1.0',
    'sequence': 1,
    'summary': '基础信息模块维护',
    'description': """
    """,
    'author': '北京迪威特',
    'website': 'http://www.bjdvt.com',
    'depends': ['base'],
    'data': [
        'views/res_location.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
}
