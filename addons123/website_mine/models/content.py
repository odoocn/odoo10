#coding:utf8
from odoo import api, fields, models, SUPERUSER_ID, _

class DvtThirdContent(models.Model):
    _name = 'dvt.third.content'
    _description = u'三级目录'
    _rec_name = 'name'
    _order = 'id DESC'

    belong_to = fields.Many2one('dvt.second.content', u'上级目录')
    name = fields.Char(u'名称')
    url = fields.Char('url')
    date = fields.Date(u'发布日期', default=fields.Date.context_today)
    html = fields.Html(u'页面内容')

class DvtSecondContent(models.Model):
    _name = 'dvt.second.content'
    _description = u'二级目录'
    _rec_name = 'name'

    belong_to = fields.Many2one('dvt.first.content', u'上级目录')
    submenu = fields.One2many('dvt.third.content', 'belong_to', u'子菜单')
    name = fields.Char(u'名称')
    url = fields.Char('url')
    type = fields.Selection([('content', u'目录'), ('details', u'内容')], u'类型')
    html = fields.Html(u'页面内容')

class DvtFirstContent(models.Model):
    _name = 'dvt.first.content'
    _description = u'一级目录'
    _rec_name = 'name'

    name = fields.Char(u'名称')
    url = fields.Char('url')
    submenu = fields.One2many('dvt.second.content', 'belong_to', u'子菜单')
    type = fields.Selection([('content', u'目录'), ('details', u'内容')], u'类型')
    html = fields.Html(u'页面内容')
    picture = fields.Binary(u'页面图片')