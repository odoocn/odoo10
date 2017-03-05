# -*- coding: utf-8 -*-

{
    'name': 'Equipments',
    'version': '1.0',
    'sequence': 125,
    'category': 'Human Resources',
    'description': """
        Track equipment and manage maintenance requests.""",
    'depends': ['mail', 'mrp_repair'],
    'summary': 'Equipments, Assets, Internal Hardware, Allocation Tracking',
    'data': [
        'security/maintenance.xml',
        'security/ir.model.access.csv',
        'data/maintenance_data.xml',
        'views/equipment_borrow.xml',
        'views/maintenance_templates.xml',
        'views/maintenance_scrap_view.xml',
        'views/equipment_transfer.xml',
        'views/maintenance_pandian.xml',
        'views/equipment_check.xml',
        'views/equipment_fault.xml',
        'views/maintenance_views.xml',

    ],
    'demo': ['data/maintenance_demo.xml'],
    'installable': True,
    'application': True,
}
