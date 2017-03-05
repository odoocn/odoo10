# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _

class EquipmentTransfer(models.Model):
    _name = 'equipment.transfer'
    _inherit = ['mail.thread']
    _description = u'设备调动'
    _rec_name = 'equipment'

    equipment = fields.Many2one('maintenance.equipment', string=u'设备名称', required=True, track_visibility='onchange')
    department_out = fields.Many2one('hr.department', string=u'调出部门')
    department_in = fields.Many2one('hr.department', string=u'调入部门', required=True)
    transfer_date = fields.Date(string=u'调动日期')
    reason = fields.Char(string=u'调动原因')
    note = fields.Text(string=u'备注')

    _default={

    }
    @api.model
    def create(self, vals):
        transfer = super(EquipmentTransfer, self).create(vals)
        transfer.equipment.write({'owner_user_id': transfer.department_in.id})
        return transfer

    @api.onchange('equipment')
    def _onchange_equipment(self):
        if self.equipment:
            self.department_out = self.equipment.owner_user_id