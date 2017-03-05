# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'APP更新',
    'version': '1.0',
    'sequence': 2,
    'description': """
    """,
    'author': '北京迪威特',
    'website': 'http://www.bjdvt.com',
    'depends': ['website'],
    'data': [
        'view.xml',
        'download_templates.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
}
