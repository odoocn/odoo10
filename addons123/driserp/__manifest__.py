# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'DRISERP',
    'version': '1.0',
    'sequence': 2,
    'summary': '电商ERP系统',
    'description': """
    """,
    'author': '北京迪威特',
    'website': 'http://www.bjdvt.com',
    'depends': ['base_plus', 'account',
                'payment', 'mrp',
                'stock_picking_wave', 'sale',
                'sale_stock', 'purchase', 'base_workflow'],
    'data': [
        'security/driserp_security.xml',
        'security/ir.model.access.csv',
        'depends/config_view.xml',
        'tools/alert_view.xml',
        'depends/product_view.xml',
        'depends/xpath.xml',
        'depends/sale_view.xml',
        'depends/stock_view.xml',
        'depends/stock_picking_wave.xml',
        'shops/qty_confirm_view.xml',
        'shops/shops_view.xml',
        'shops/express_view.xml',
        'shops/return_views.xml',
        'shops/order_track_view.xml',
        'shops/data_view.xml',
        'tools/error_info_view.xml',
        'report/deriserp_report.xml',
        'report/report_product_template.xml',
        'shops/menuitem.xml',
        'data/plate_data.xml',
        'data/stock_data.xml',
        'data/express_data.xml',
        'data/auto_mission.xml',
    ],
    'qweb': [
        'static/src/xml/sale_buttons.xml',
    ],
    'installable': True,
    'application': True,
}
