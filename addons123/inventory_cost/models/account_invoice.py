# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import datetime
from odoo.exceptions import UserError, ValidationError

class inventory_account_invoice(models.Model):

    _inherit = "account.invoice"

    # state = fields.Selection(selection_add=[('balance', u'已结算')])
    balance_flg = fields.Boolean(u"是否结算")

    @api.multi
    def account_invoice_balance(self):
        #  结算
        purchase_ids = []
        for invoice_line in self.invoice_line_ids:
            purchase_ids.append(invoice_line.purchase_line_id.order_id.id)
        purchase_ids = list(set(purchase_ids))
        # 取得入库明细
        stock_move_lines = self.env["stock.move"].search([('send_receive_type.purchase_in', '=', 'purchase_in'), ('state', '=', 'done'), ('account_type', '=', '0'), ('purchase_id', 'in', purchase_ids)])
        if stock_move_lines and len(stock_move_lines) == len(self.invoice_line_ids):
            # 生成结算单
            values = {
                'balance_date': datetime.datetime.now(),
                'invoice_line_ids': [(4, self.invoice_line_ids.ids, False)],
                'stock_move_ids': [(4, stock_move_lines.ids, False)],
                'state': 'balance'
            }
            inventory_balance = self.env["inventory.balance"].create(values)
            inventory_balance.button_balance()
        else:
            raise ValidationError("采购订单没有入库，无法结算！")
        return self.update({'balance_flg': True})


class inventory_account_invoice_line(models.Model):

    _inherit = "account.invoice.line"
    state = fields.Selection([('unbalance', u'未结算'), ('balance', u'已结算')], string=u"状态")
