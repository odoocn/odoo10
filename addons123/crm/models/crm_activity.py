# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class CrmActivity(models.Model):
    ''' CrmActivity is a model introduced in Odoo v9 that models activities
    performed in CRM, like phone calls, sending emails, making demonstrations,
    ... Users are able to configure their custom activities.

    Each activity can configure recommended next activities. This allows to model
    light custom workflows. This way sales manager can configure their crm
    workflow that salepersons will use in their daily job.

    CrmActivity inherits from mail.message.subtype. This allows users to follow
    some activities through subtypes. Each activity will generate messages with
    the matching subtypes, allowing reporting and statistics computation based
    on mail.message.subtype model. '''

    _name = 'crm.activity'
    _description = 'CRM Activity'
    _rec_name = 'name'
    _order = "start_time,plane_start_time"

    @api.multi
    def get_execute(self):
        return self.env.user

    name = fields.Char(string=u'目的', required=True)
    user_id = fields.Many2one('res.users', string=u'执行人', default=get_execute, required=True)
    u_idid = fields.Integer(string=u'用户ID', compute="compute_users")
    way = fields.Selection([('1', '电话'),
                            ('2', '现场'),
                            ('3', '邮件'),
                            ('4', '信息沟通')], u'活动方式')
    # 计划时间
    plane_start_time = fields.Datetime(u'开始时间', required=True)
    plane_end_time = fields.Datetime(u'结束时间', required=True)
    # 执行时间
    start_time = fields.Datetime(u'开始时间')
    end_time = fields.Datetime(u'结束时间')
    # 日历时间
    cal_start_time = fields.Datetime()
    cal_end_time = fields.Datetime()
    place = fields.Char(u'地点')
    partner_id = fields.Many2one('res.partner', u'客户', domain="[('customer','=',True)]")
    meeting = fields.Char(u'会见人')
    opportunity = fields.Many2one('crm.lead', u'商机')
    evaluation = fields.Text(u'活动效果自我评价')
    next_plan = fields.Text(u'下一步计划')
    state = fields.Selection([('unfinished', '活动未完成'), ('finished', '活动完成')], string=u'状态',
                             compute='compute_state', store=True,
                             default='unfinished')
    start_date = fields.Date(compute='compute_date', store=True)
    end_date = fields.Date(compute='compute_date', store=True)

    @api.depends('plane_start_time', 'plane_end_time', 'start_time')
    def compute_date(self):
        for r in self:
            if r.start_time:
                r.start_date = fields.Date.from_string(r.start_time)
            else:
                r.start_date = fields.Date.from_string(r.plane_start_time)
                r.end_date = fields.Date.from_string(r.plane_end_time)

    @api.onchange('cal_start_time', 'cal_end_time')
    def onchange_cal(self):
        if not self.start_time or not self.end_time:
            self.plane_start_time = self.cal_start_time
            self.plane_end_time = self.cal_end_time

    @api.model
    def create(self, vals):
        if vals['plane_start_time'] != vals['cal_start_time']:
            vals['cal_start_time'] = vals['plane_start_time']
        if vals['plane_end_time'] != vals['cal_end_time']:
            vals['cal_end_time'] = vals['plane_end_time']
        if vals.get('start_time') and vals.get('end_time'):
            vals['cal_start_time'] = vals['start_time']
            vals['cal_end_time'] = vals['end_time']
        return super(CrmActivity, self).create(vals)

    @api.multi
    def write(self, vals):
        if (vals.get('plane_start_time') or vals.get('plane_end_time')) and not self.end_time and\
                not vals.get('end_time'):
            # 未完成时对计划时间做修改
            if vals.get('plane_start_time'):
                vals['cal_start_time'] = vals['plane_start_time']
            if vals.get('plane_end_time'):
                vals['cal_end_time'] = vals['plane_end_time']
        elif vals.get('end_time') or vals.get('start_time'):
            # 填报执行时间或修改执行时间时
            if vals.get('start_time'):
                vals['cal_start_time'] = vals['start_time']
            if vals.get('end_time'):
                vals['cal_end_time'] = vals['end_time']
        elif vals.get('cal_start_time') or vals.get('cal_end_time'):
            # 由拖动引发
            if self.start_time and self.end_time:
                if vals.get('cal_start_time'):
                    vals['start_time'] = vals['cal_start_time']
                if vals.get('cal_end_time'):
                    vals['end_time'] = vals['cal_end_time']
            else:
                if vals.get('cal_start_time'):
                    vals['plane_start_time'] = vals['cal_start_time']
                if vals.get('cal_end_time'):
                    vals['plane_end_time'] = vals['cal_end_time']
        return super(CrmActivity, self).write(vals)

    @api.depends('start_time', 'end_time')
    def compute_state(self):
        for r in self:
            if r.start_time and r.end_time:
                r.state = 'finished'
            else:
                r.state = 'unfinished'

    @api.depends('user_id')
    def compute_users(self):
        for r in self:
            r.u_idid = r.user_id.id

    @api.multi
    def close_dialog(self):
        return {'type': 'ir.actions.act_window_close'}

    # @api.multi
    # def unlink(self):
    #     activities = self.search([('subtype_id', '=', self.subtype_id.id)])
    #     # to ensure that the subtype is only linked the current activity
    #     if len(activities) == 1:
    #         self.subtype_id.unlink()
    #     return super(CrmActivity, self).unlink()
