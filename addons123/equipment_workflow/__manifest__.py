# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': '设备 工作流配置',
    'version': '1.0',
    'sequence': 1,
    'summary': '工作流配置',
    'description': """
    """,
    'author': '北京迪威特',
    'website': 'http://www.bjdvt.com',
    'depends': ['hr', 'base', 'maintenance', 'vnsoft_form_hide_edit'],
    'data': [
        'security/ir.model.access.csv',
        'views/workflow_view.xml',
        'views/workflow_history_view.xml',
        'views/workflow_maintenance_scrap_view.xml',
    ],
    'installable': True,
    'application': True,
}
