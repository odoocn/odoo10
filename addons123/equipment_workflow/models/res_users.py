# -*- coding: utf-8 -*-

from odoo import fields, models
from odoo import api


class res_users_employee(models.Model):
    _inherit = "res.users"
    employee_id = fields.Many2one('hr.employee', u'员工')


class res_employee_user(models.Model):
    _inherit = "hr.employee"
    parent_id = fields.Many2one("hr.employee", related='department_id.manager_id', readonly=True, string=u'部门主管')

    @api.model
    def create(self, values):
        # 选择用户后自动跟新users表的员工字段
        result = super(res_employee_user, self).create(values)
        if result.user_id:
            user = self.env['res.users'].search([('id', '=', result.user_id.id)])
            user.update({"employee_id": result.id})
        return result

    @api.multi
    def write(self, values):
        result = super(res_employee_user, self).write(values)
        for employee in self:
            if employee.user_id:
                user = self.env['res.users'].search([('id', '=', employee.user_id.id)])
                user.update({"employee_id": employee.id})
        return result