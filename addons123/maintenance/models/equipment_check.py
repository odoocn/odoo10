# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _

class EquipmentCheck(models.Model):

    _name = 'equipment.check'
    _inherit = ['mail.thread']
    _description = u'设备检查点'

    name = fields.Char(string=u"检查点名称", required=True)
    equipment = fields.Many2one('maintenance.equipment', string=u'设备名称', required=True)
    state = fields.Selection([('1', u'正常'), ('0', u'异常')], string=u'检查点状态', default='1')
    place = fields.Char(string=u'地点')
    code = fields.Char(string=u'条码', required=True)
    description = fields.One2many('equipment.description', 'check_point', string=u'任务描述')
    result = fields.One2many('equipment.check.result', 'equipment_check_id', string=u'巡检结果')
    color = fields.Integer('Color Index')
    result_count = fields.Integer(compute='_compute_result_count', string=u"巡检结果数量", store=True)

    @api.one
    @api.depends('result')
    def _compute_result_count(self):
        self.result_count = len(self.result)


class EquipmentDescription(models.Model):
    _name = 'equipment.description'
    _description = u'检查任务'
    _rec_name = 'check_point'

    check_point = fields.Many2one('equipment.check', string=u'检查点名称', required=True, ondelete='cascade')
    name = fields.Char(string=u'名称')
    description = fields.Text(string=u'任务描述')


class EquipmentLine(models.Model):

    _name = 'equipment.line'
    _inherit = ['mail.thread']
    _description = u'设备巡检路线'
    _rec_name = 'name'

    name = fields.Char(string='线路名称', required=True)
    check_user = fields.Many2one('res.users', string=u'负责人', required=True)
    check_point = fields.Many2many('equipment.check', string=u'设备检查点', required=True)
    plan = fields.One2many('equipment.plan', 'equipment_line', string=u'巡查计划')


class EquipmentPlan(models.Model):

    _name = 'equipment.plan'
    _description = u'设备巡检计划'
    _rec_name = 'equipment_line'

    equipment_line = fields.Many2one('equipment.line', string=u'设备巡检路线', required=True, ondelete='cascade')
    week = fields.Selection([('1', '星期一'), ('2', '星期二'), ('3', '星期三'), ('4', '星期四'), ('5', '星期五'), ('6', '星期六'), ('0', '星期天'), ], string='星期')
    hour_from = fields.Float(string=u'工作起始', required=True)
    hour_to = fields.Float(string=u'工作截止', required=True)
    line_name = fields.Char(related='equipment_line.name', string=u"线路名称", readonly=True)
    check_user = fields.Many2one(related="equipment_line.check_user", string=u'负责人', readonly=True)


class EquipmentCheckResult(models.Model):
    _name = "equipment.check.result"
    _description = u'设备巡检结果'
    _rec_name = "equipment_check_id"

    equipment_check_id = fields.Many2one("equipment.check", string=u'检查点', required=True)
    state = fields.Selection([("1", "正常"), ("2", "异常")], string=u'状态')
    check_user = fields.Many2one('res.users', string=u'检查人', required=True)
    check_time = fields.Datetime(string=u'检查时间')
    note = fields.Text(string=u'描述')

    @api.model
    def create(self, values):
        if values['state'] == "2":
            self.env['equipment.check'].search([('id', '=', values['equipment_check_id'])]).state = "0"
        else:
            self.env['equipment.check'].search([('id', '=', values['equipment_check_id'])]).state = "1"
        return super(EquipmentCheckResult, self).create(values)

    @api.multi
    def write(self, value):
        if "state" in value:
            if value['state'] == "2":
                # 更新设备点状态为异常
                self.equipment_check_id.state = "0"
            else:
                self.equipment_check_id.state = "1"
        return super(EquipmentCheckResult, self).write(value)