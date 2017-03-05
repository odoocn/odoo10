# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo import api, _


class res_workflow_history(models.Model):
    _name = "res.workflow.history"
    _order = "handle_time desc"
    model = fields.Char(u'模块名')
    model_name = fields.Char(u'单据类型')
    res_id = fields.Integer(u'来源ID')
    into_person = fields.Many2one('res.users', u'转入人')
    into_time = fields.Datetime(u'转入时间')
    auditor_id = fields.Many2one('res.users', u'审核人')
    handle_time = fields.Datetime(u'处理时间')
    handle_result = fields.Char(u'审核结果')   # 审核结果（提交，撤回，通过，驳回）
    handle_reason = fields.Text(u'原因')
    handle_type = fields.Selection([('need', '待办'), ('history', '历史')], u'处理状态')
    submit_person = fields.Many2one('res.users', u'提交人')
    remark = fields.Text(u'备注')

