# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _

class EquipmentBorrow(models.Model):
    _name = 'equipment.borrow'
    _inherit = ['mail.thread']
    _description = u'设备借用'
    _rec_name = 'equipment'

    equipment = fields.Many2one('maintenance.equipment', string=u'设备名称', required=True)
    department = fields.Many2one('hr.department', string=u'借用部门', required=True)
    employee = fields.Many2one('hr.employee', string=u'借用人')
    borrow_date = fields.Date(string=u'借用日期')
    reason = fields.Char(string=u'借用原因')
    return_date = fields.Date(string=u'预计归还日期')
    note = fields.Text(string=u'备注')
    state = fields.Selection([('borrow', u'借用中'), ('return', u'已归还')], string=u'状态', default='borrow')


    @api.model
    def create(self, vals):
        borrow = super(EquipmentBorrow, self).create(vals)
        borrow.equipment.write({'state': '1'})
        return borrow

    @api.multi
    def return_equipment(self):
        self.write({'state': 'return'})
        self.equipment.write({'state': '0'})
        return None