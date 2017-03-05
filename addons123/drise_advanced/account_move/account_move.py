# encoding=utf-8
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    analytic_account_id = fields.Many2one('account.analytic.account', related='line_ids.analytic_account_id',
                                          string=u'分析账户')
