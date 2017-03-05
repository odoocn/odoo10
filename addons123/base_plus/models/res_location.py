# -*- coding: utf-8 -*-
from odoo import api, models, fields


class ResProvince(models.Model):
    _name = "res.province"
    name = fields.Char(string=u'名称', required=True)
    code = fields.Char(string=u'编码')
    city = fields.One2many('res.city', 'province_id', string=u'下级市区')

    @api.multi
    def get_province(self, name):
        if not name:
            return False
        res = self.search([('name', 'ilike', name)])
        if res:
            return res[0].id
        else:
            return self.create({'name': name}).id


class ResCity(models.Model):
    _name = "res.city"
    name = fields.Char(string=u'名称', required=True)
    code = fields.Char(string=u'编码')
    province_id = fields.Many2one('res.province', string=u'上级省市')
    district = fields.One2many('res.district', 'city_id', string=u'下级区县')

    @api.multi
    def get_city(self, name):
        if not name:
            return False
        res = self.search([('name', 'ilike', name)])
        if res:
            return res[0].id
        else:
            return self.create({'name': name}).id


class ResDistrict(models.Model):
    _name = "res.district"
    name = fields.Char(string=u'名称', required=True)
    code = fields.Char(string=u'编码')
    city_id = fields.Many2one('res.city', string=u'上级市区')

    @api.multi
    def get_district(self, name):
        if not name:
            return False
        res = self.search([('name', 'ilike', name)])
        if res:
            return res[0].id
        else:
            return self.create({'name': name}).id
