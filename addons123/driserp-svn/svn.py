# encoding:utf-8
from odoo import fields, api, models


class DriserpSvn(models.Model):
    _name = 'driserp.svn'
    _description = 'svn'

    name = fields.Char(string=u'环境名称')
    url = fields.Char(string=u'环境地址', help='192.168.1.1')
    user_name = fields.Char(string=u'用户名')
    password = fields.Char(string=u'密码')
    port = fields.Integer(string=u'端口')
    svn_code = fields.Char(string=u'SVN路径')
    note = fields.Text(string=u'备注')
    database = fields.Char(string=u'数据库名称')
    database_port = fields.Integer(string=u'数据库端口')
    database_user = fields.Char(string=u'数据库用户')
    database_password = fields.Char(string=u'数据库用户密码')
