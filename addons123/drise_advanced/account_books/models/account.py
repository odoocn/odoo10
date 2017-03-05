# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import time


class DAOtherAccounting1(models.Model):
    _name = "account.other.accounting1"

    name = fields.Char(u'名称', required=True)
    description = fields.Text(u'描述')


class DAOtherAccounting2(models.Model):
    _name = "account.other.accounting2"

    name = fields.Char(u'名称', required=True)
    description = fields.Text(u'描述')


class DACashFlowType(models.Model):
    _name = 'cash.flow.type'

    name = fields.Char(u'名称', required=True)
    description = fields.Text(u'描述')


class DACashFlowItem(models.Model):
    _name = "account.cash.flow"

    name = fields.Char(u'名称', required=True)
    description = fields.Text(u"描述")
    type_id = fields.Many2one('cash.flow.type', string=u'现金流量项类型', required=True)


class DAAccountAccount(models.Model):
    _inherit = "account.account"

    department_accounting = fields.Boolean(string=u'部门核算', default=False)
    analytic_accounting = fields.Boolean(string=u'分析账户核算', default=False)
    partner_accounting = fields.Boolean(string=u'业务伙伴核算', default=False)

    other_accounting1 = fields.Boolean(string=u'扩展核算方式1', default=False)
    other_accounting2 = fields.Boolean(string=u'扩展核算方式2', default=False)

    accounting_uneditable = fields.Boolean(string=u'  ', compute='compute_editable')

    @api.one
    def compute_editable(self):
        if len(self.env['account.move.line'].search([('account_id', '=', self.id)])) > 0:
            self.accounting_uneditable = True
        else:
            self.accounting_uneditable = False


class DAAccountMoveLine(models.Model):
    _inherit = "account.move.line"

    department_id = fields.Many2one('hr.department', string=u'部门')
    other_accounting1 = fields.Many2one("account.other.accounting1", string=u'扩展辅助核算1')
    other_accounting2 = fields.Many2one("account.other.accounting2", string=u'扩展辅助核算2')

    cash_flow_item = fields.Many2one("account.cash.flow", string=u'现金流量项')

    accounting_details = fields.Text(string=u'辅助核算', compute='compute_accounting_details')

    @api.one
    def compute_accounting_details(self):
        for r in self:
            details = []
            if r.partner_id and r.account_id.partner_accounting:
                details.append(r.partner_id.name)
            elif r.account_id.partner_accounting:
                details.append(u'业务伙伴未指定')
            if r.analytic_account_id and r.account_id.analytic_accounting:
                details.append(r.analytic_account_id.name)
            elif r.account_id.analytic_accounting:
                details.append(u'分析账户未指定')
            if r.department_id and r.account_id.department_accounting:
                details.append(r.department_id.name)
            elif r.account_id.department_accounting:
                details.append(u'部门未指定')
            if r.other_accounting1 and r.account_id.other_accounting1:
                details.append(r.other_accounting1.name)
            elif r.account_id.other_accounting1:
                details.append(u'扩展辅助项1未指定')
            if r.other_accounting2 and r.account_id.other_accounting2:
                details.append(r.other_accounting2.name)
            elif r.account_id.other_accounting2:
                details.append(u'扩展辅助项2未指定')
            if r.account_id.user_type_id.type == 'liquidity' and not r.cash_flow_item:
                details.append(u'现金流量项目未指定')
            r.accounting_details = ';'.join(details)
        return True

    @api.multi
    def action_accounting_set(self):
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('drise_advanced.action_accounting_set_menu')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_mode': action.view_mode,
            'view_id': action.view_id.id,
            'target': action.target,
            'res_model': action.res_model,
            'context': {'default_move_line_id': self.id}
        }
        return result
