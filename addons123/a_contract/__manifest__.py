# -*- coding: utf-8 -*-
# 作者：孙志恒 ；日期：2016年10月10日；版本：V1.0；更新：2016年10月10日；

{
    "name": "合同管理",
    "version": "1.0",
    "author": "nike sun",
    "sequence": 0,
    "summary": """合同管理""",
    "website": "http://www.baidu.com",
    "depends": ['base', 'account', 'product', 'sale', 'mail'],
    "data": [
        'views/contract_type_view.xml',
        'views/contract_view.xml',
        'views/ir_attachment_view.xml',
        # 'views/shop_view.xml',
        'views/contract_change_history.xml',
        # 'views/mail_template_data.xml',
    ],

    "installable": True,
    'application': True,
    "category": 'Generic Modules/Others'
}
