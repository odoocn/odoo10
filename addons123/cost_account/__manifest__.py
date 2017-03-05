# coding:utf-8
{
    'name': 'cost_account',
    'description': 'cost accounting',
    'version0': '1.0',
    'author': 'mlp',
    'sequence': '2',
    'website': 'http://www.bjdvt.com',
    'summary': 'cost account',
    'depends': ['base', 'hr', 'product', 'stock',
                'inventory_cost', 'mrp',
                ],
    'data': [
        'views/cost.xml',
        'views/cost_data_fill.xml',
        'views/cost_expense.xml',
        'views/cost_account_algorithm_view.xml'
    ],
    'qweb': [

    ],

    'installable': True,

    'application': True,

    'category': 'Generic Modules/Others'

}
