# -*- coding: utf-8 -*-
from odoo import fields, models, api


class dvt_crm_source(models.Model):
    _name = "dvt.crm.source"
    name = fields.Char('来源')
    situation = fields.Text('详情', compute='compute_situation', store=True)
    others = fields.Boolean('是否需要独立说明')

    @api.depends('name')
    def compute_situation(self):
        for r in self:
            if not r.situation:
                r.situation = r.name
