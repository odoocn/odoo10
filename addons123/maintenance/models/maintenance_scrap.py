# -*- coding: utf-8 -*-

from datetime import date, datetime, timedelta
from odoo.exceptions import UserError
from odoo import api, fields, models, SUPERUSER_ID, _


class MaintenanceScrap(models.Model):
    _name = "maintenance.scrap"
    _description = u"设备报废申请"
    _rec_name = "maintenance_id"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    def _get_apply_user(self):
        return self.env.user.id

    maintenance_id = fields.Many2one("maintenance.equipment", string=u"设备名称", required=True, readonly=True, states={'1': [('readonly', False)], '3': [('readonly', False)], '4': [('readonly', False)]})
    state = fields.Selection([("1", "报废"), ("5", "确认报废")], string=u"状态", default="1")
    maintenance_state = fields.Char(u"设备报废前状态")
    scrap_reason = fields.Text(u"报废原因", readonly=True, states={'1': [('readonly', False)], '3': [('readonly', False)], '4': [('readonly', False)]})
    apply_user = fields.Many2one("res.users", string=u"申请人", readonly=True, states={'1': [('readonly', False)], '3': [('readonly', False)], '4': [('readonly', False)]})

    @api.multi
    def unlink(self):
        for scrap in self:
            if scrap.state != "1" or scrap.state != "3":
                raise UserError("单据无法删除")
        return super(MaintenanceScrap, self).unlink()

    def button_ok(self):
        # 更新设备表
        equipment = self.env['maintenance.equipment'].search([('id', '=', self.maintenance_id.id)])
        if equipment:
            equipment.update({"state": "4"})
        self.update({'state': "5"})
