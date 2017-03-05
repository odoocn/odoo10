# -*- coding: utf-8 -*-
from odoo import fields, models, api


class dvt_compare_line(models.Model):
    _name = "dvt.compare.line"

    contact = fields.Many2one('dvt.compare.contact', string="关键人", required=True)
    compare = fields.Many2one('dvt.compare', string='竞争对手', required=True)
    valid = fields.Boolean('有效', default=True)
    opportunity = fields.Many2one('crm.lead', string='商机ID')

    @api.multi
    def cancel_compare(self):
        self.write({'valid': False})


class dvt_compare_relationship(models.Model):
    _name = "dvt.compare.relationship"

    name1 = fields.Many2one('dvt.compare.contact', u'主关键人')
    name2 = fields.Many2one('dvt.compare.contact', u'关键人')
    name2_company = fields.Many2one('dvt.compare', related='name2.company', string=u'所在公司')
    name2_dep = fields.Char(string=u'部门', related='name2.dep')
    relationship = fields.Selection([('0', '亲密'), ('1', '一般'), ('2', '紧张')], string=u'关系')
    details = fields.Char(u'说明')


class dvt_compare(models.Model):
    _name = "dvt.compare"

    name = fields.Char(u'名称', required=True)
    register = fields.Date(u'注册时间')
    shareholder = fields.Char(u'股东构成')
    intelligence = fields.Char(u'资质情况')
    service = fields.Text(u'主要业务')
    product = fields.Text(u'产品情况')
    self_relation = fields.Char(u'与本公司竞争情况')
    contact = fields.One2many('dvt.compare.contact', 'company', string=u'关键人')


class dvt_compare_contact(models.Model):
    _name = "dvt.compare.contact"

    name = fields.Char(u'姓名', required=True)
    sex = fields.Selection([('1', '男'), ('2', '女')], u'性别')

    birth = fields.Char(u'籍贯')
    school = fields.Char(u'毕业学校')
    marriage = fields.Char(u'婚姻状况')
    contact = fields.Char(u'联系方式')
    address = fields.Char(u'家庭住址')
    others = fields.Text(u'备注')
    dep = fields.Char(u'部门')
    company = fields.Many2one('dvt.compare', u'公司')
    job = fields.Char(u'职位')
    relationship = fields.One2many('dvt.compare.relationship', 'name1', string=u'关系')
