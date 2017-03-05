# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError


class EquipmentFault(models.Model):
    _name = 'equipment.fault'
    _inherit = ['mail.thread']
    _description = u'设备故障'

    name = fields.Char(string=u'名称', required=True)
    equipment = fields.Many2one('maintenance.equipment', string=u'设备名称', required=True)
    equipment_check = fields.Many2one('equipment.check', string=u'设备巡检点')
    reporter = fields.Many2one('res.users', string=u'报修人', required=True)
    transactor = fields.Many2one('res.users', string=u'处理人')
    report_time = fields.Datetime(string=u'报修时间')
    transact_time = fields.Datetime(string=u'处理时间')
    state = fields.Selection([('ing', u'处理中'), ('ed', u'已处理')], default='ing')
    fault_type = fields.Many2one("equipment.fault.type", string=u'故障类型')
    note = fields.Text(string=u"故障描述")

    @api.model
    def create(self, vals):
        fault = super(EquipmentFault, self).create(vals)
        fault.equipment.write({'state': '5'})
        fault.equipment_check.write({'state': '0'})

        # 设备故障后，给关注着推送消息
        for follower in fault.equipment.message_follower_ids:
            fault.equipment.message_post(
                body=_("%s 设备的 %s 巡检点发生故障，提交人 %s !") % (fault.equipment.name, fault.equipment_check.name, fault.transactor.partner_id.name),
                subject="RE:设备故障提醒",
                message_type="comment",
                content_subtype='html', partner_ids=follower.partner_id.ids, subtype_ids=1)

        return fault

    # 处理完成
    @api.multi
    def ignore(self):
        if self.transactor:
            if self.state == 'ing':
                self.write({'state': 'ed'})
                self.equipment_check.write({'state': '1'})
                if not self.search([('equipment', '=', self.equipment.id), ('state', '=', 'ing')]):
                    self.equipment.write({"state": '0'})
                    # 设备故障后，给关注着推送消息
                    for follower in self.equipment.message_follower_ids:
                        self.equipment.message_post(
                            body=_("%s 设备的 %s 巡检点的故障已修复，处理人 %s !") % (
                                self.equipment.name, self.equipment_check.name, self.reporter.partner_id.name),
                            subject="RE:设备故障修复提醒",
                            message_type="comment",
                            content_subtype='html', partner_ids=follower.partner_id.ids, subtype_ids=1)
        else:
            raise UserError("处理人不能为空")

        return True

    # 生成修理单
    @api.multi
    def repair(self):
        if self.state == 'ing':
            vals = {
                'maintenance_id': self.equipment.id,
                'repair_data': self.transact_time,
            }
            self.env['mrp.repair'].create(vals)
            self.equipment.write({"state": '0'})
            # self.equipment.write({"state": '0'})
        return True


class equipment_fault_type(models.Model):
    _name = "equipment.fault.type"
    _description = u"故障类型"

    name = fields.Char(string="类型")