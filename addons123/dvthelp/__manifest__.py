#coding:utf-8
{
    'name':'odoo-help',
    'description':'help to uederstand',
    'version0':'1.0',
    'author':'mlp',
    'sequence':'2',
    'website':'http://www.bjdvt.com',
    'summary': 'help to know odoo',
    'depends':['base','web','hr'
               ],
    'data':[
        "views/help_title.xml",
        'views/website.xml',
        'views/xpath.xml',
        'views/hr_change.xml',
    ],
    'qweb' : [
        "static/src/xml/add_help.xml",
    ],



    'installable' : True,

    'application': True,

    'category':'Generic Modules/Others'


}
