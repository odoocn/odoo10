# -*- coding: utf-8 -*-

from odoo import api, fields, models


class DAAccountingSet(models.TransientModel):
    _name = "accounting.set"

    move_line_id = fields.Many2one('account.move.line', string=u'会计分录行')
    account_id = fields.Many2one('account.account', related='move_line_id.account_id', string=u'会计科目')
    department_accounting = fields.Boolean(related='account_id.department_accounting', string=u'部门核算')
    department_id = fields.Many2one('hr.department', string=u'部门')
    analytic_accounting = fields.Boolean(related='account_id.analytic_accounting', string=u'分析账户核算')
    analytic_id = fields.Many2one('account.analytic.account', string=u'分析账户')
    partner_accounting = fields.Boolean(related='account_id.partner_accounting', string=u'业务伙伴核算')
    partner_id = fields.Many2one('res.partner', string=u'业务伙伴')

    other_choice1 = fields.Boolean(string=u'扩展辅助核算1启用')
    other_accounting1 = fields.Many2one("account.other.accounting1", string=u'扩展辅助核算1')

    other_choice2 = fields.Boolean(string=u'扩展辅助核算2启用')
    other_accounting2 = fields.Many2one("account.other.accounting2", string=u'扩展辅助核算2')

    liquidityable = fields.Boolean(string=u'可设定现金流量')
    cash_flow_item = fields.Many2one("account.cash.flow", string=u'现金流量项')

    @api.onchange('move_line_id')
    def onchange_move_line(self):
        self.department_id = self.move_line_id.department_id.id
        self.analytic_id = self.move_line_id.analytic_account_id.id
        self.partner_id = self.move_line_id.partner_id.id

        self.other_choice1 = self.account_id.other_accounting1
        self.other_accounting1 = self.move_line_id.other_accounting1.id

        self.other_choice2 = self.account_id.other_accounting2
        self.other_accounting2 = self.move_line_id.other_accounting2.id

        if self.account_id.user_type_id.type == 'liquidity':
            self.liquidityable = True
        else:
            self.liquidityable = False
        self.cash_flow_item = self.move_line_id.cash_flow_item.id

    @api.multi
    def confirm_setting(self):
        self.move_line_id.write({"department_id": self.department_id.id if self.department_id else False,
                                 "analytic_account_id": self.analytic_id.id if self.analytic_id else False,
                                 "partner_id": self.partner_id.id if self.partner_id else False,
                                 "other_accounting1": self.other_accounting1.id if self.other_accounting1 else False,
                                 "other_accounting2": self.other_accounting2.id if self.other_accounting2 else False,
                                 "cash_flow_item": self.cash_flow_item.id if self.cash_flow_item else False})
        return True
