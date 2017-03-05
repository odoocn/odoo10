#coding:utf8
from odoo import api, fields, models, SUPERUSER_ID, _

class DvtNew(models.Model):
    _name = 'dvt.new'
    _description = u'新闻'
    _rec_name = 'name'

    name = fields.Char(u'名称')
    number = fields.Integer(u'编号')
    type = fields.Many2one('dvt.product.type', u'产品类型')
    description = fields.Text(u'产品描述')