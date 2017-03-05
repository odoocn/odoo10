#coding:utf8
from odoo import api, fields, models, SUPERUSER_ID, _

class DvtProduct(models.Model):
    _name = 'dvt.product'
    _description = u'产品'
    _rec_name = 'name'

    name = fields.Char(u'名称')
    number = fields.Integer(u'编号')
    type = fields.Many2one('dvt.product.type', u'产品类型')
    description = fields.Text(u'产品描述')


class DvtProductType(models.Model):
    _name = 'dvt.product.type'
    _rec_name = 'type'


    type = fields.Char(u'产品类别')
