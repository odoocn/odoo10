#coding:utf-8
{
    'name': '我的网站',
    'description': u'我的网站模块',
    'version0': '1.0',
    'author': 'lxm',
    'sequence': '1',
    'website': '',
    'summary': u'我的网站',
    'depends': ['base', 'web', 'website'],
    'data': [
        "views/templates.xml",
        "data/mine_data.xml",
    ],
    'qweb': [
    ],

    'installable': True,

    'application': True,

    'category': 'Generic Modules/Others'

}
