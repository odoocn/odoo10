# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp
from odoo.tools import float_utils

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    # state=fields.Selection([('1','调拨'),('2','借用'),('3','报废'),('4','封存'),('5','维修')],string='状态')
    inventory_id=fields.Many2one('maintenance.check')

class MaintenanceCheck(models.Model):
    _name='maintenance.check'

    name = fields.Char(
       u'盘点参考',
        readonly=True, required=True,
        states={'draft': [('readonly', False)]})
    date = fields.Datetime(
        u'盘点时间',
        readonly=True, required=True,
        default=fields.Datetime.now,
        help="The date that will be used for the stock level check of the products and the validation of the stock move related to this inventory.")
    line_ids = fields.One2many(
        'maintenance.equipment', 'inventory_id', string='盘点',
        copy=True, readonly=False,
        states={'done': [('readonly', True)]})

    filter=fields.Selection([('1','所有设备'),('2','手动创建设备')],
                            required=True,
                            default='1',states={'done':[('readonly',True)]})

    state = fields.Selection(string='状态', selection=[
        ('draft', '草稿'),
        ('cancel', '已取消'),
        ('confirm', '进行中'),
        ('done', '已验证')],
        copy=False, index=True, readonly=True,
        default='draft')

    @api.multi
    def prepare_inventory(self):
        vals = {'state': 'confirm', 'date': fields.Datetime.now()}
        self.write(vals)
        if self.filter =='1' and not self.line_ids:
            equips=self.env['maintenance.equipment'].search([])
            for equip in equips:
                equip.inventory_id=self.id


    @api.multi
    def action_done(self):
        self.write({'state': 'done'})

    @api.multi
    def action_cancel_draft(self):
        self.write({
            'line_ids': [(5,)],
            'state': 'draft'
        })