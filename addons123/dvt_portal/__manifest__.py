#coding:utf-8
{
    'name': '公司门户网站',
    'description': u'在外部网站动态加载数据库信息',
    'version0': '1.0',
    'author': 'lxm',
    'sequence': '3',
    'website': 'http://www.bjdvt.com',
    'summary': u'外部网站',
    'depends': ['base','web','hr'],
    'data': [
        "views/product.xml",
        "views/content.xml",
        "views/templates.xml",
    ],
    'qweb': [
    ],

    'installable': True,

    'application': True,

    'category': 'Generic Modules/Others'

}
