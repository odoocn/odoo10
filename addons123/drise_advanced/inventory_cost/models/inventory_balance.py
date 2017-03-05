# -*- coding: utf-8 -*-
from odoo import api, _, fields, models
from odoo.exceptions import UserError, ValidationError
import datetime


class inventory_balance(models.Model):
    _name = "inventory.balance"
    _rec_name = "code"
    code = fields.Char(u'结算号')
    balance_date = fields.Date(u'结算日期')
    supplier = fields.Char(u'供应商')
    purchase_type = fields.Char(u'采购类型')
    # 开票行
    invoice_line_ids = fields.Many2many('account.invoice.line', string='发票明细', readonly=True, states={'draft': [('readonly', False)]})
    # 库存移动单
    stock_move_ids = fields.Many2many('stock.move', string='入库单明细')
    state = fields.Selection([('draft', '草稿'), ('balance', '已结算'), ('account', '已记账')], default="draft", string=u'状态')
    share_type = fields.Selection([('by_value', '按金额分摊'), ('by_count', '按数量分摊')], string=u"分摊方式", default="by_count")

    # 按照选中入库单的金额分摊
    @api.multi
    def share_by_value(self):
        purchase_share_obj = {}
        purchase_share_amount = {}
        # 金额分摊率
        share_amount, be_shared_amount = self._get_share_invoice_line(self.invoice_line_ids, "by_value")
        for invoice_line in self.invoice_line_ids:
            if invoice_line.purchase_line_id and invoice_line.product_id.type != "service":
                amount = (invoice_line.price_subtotal + be_shared_amount * (invoice_line.price_subtotal / share_amount))
                purchase_share_obj[invoice_line.purchase_line_id.id] = amount / invoice_line.quantity
                purchase_share_amount[invoice_line.purchase_line_id.id] = amount
        return purchase_share_obj, purchase_share_amount

    # 按照选中入库单的数量分摊
    @api.multi
    def share_by_count(self):
        purchase_share_obj = {}
        purchase_share_amount = {}
        # 取得所有有单据的总数量
        share_count, be_shared_amount = self._get_share_invoice_line(self.invoice_line_ids, "by_count")
        for invoice_line in self.invoice_line_ids:
            if invoice_line.purchase_line_id and invoice_line.product_id.type != "service":
                amount = (invoice_line.price_subtotal + be_shared_amount * (invoice_line.quantity / share_count))
                purchase_share_obj[invoice_line.purchase_line_id.id] = amount / invoice_line.quantity
                purchase_share_amount[invoice_line.purchase_line_id.id] = amount
        return purchase_share_obj, purchase_share_amount

    # 验证上下选择的数据是否一致
    @api.multi
    def _check_consistent(self, invoice_lines, stock_move_lines):
        invoice_purchase = []
        for invoice_line in invoice_lines:
            if invoice_line.purchase_line_id and invoice_line.product_id.type != "service":
                invoice_purchase.append(invoice_line.purchase_line_id.id)
        stock_move_purchase = []
        for stock_move_line in stock_move_lines:
            if stock_move_line.purchase_line_id:
                stock_move_purchase.append(stock_move_line.purchase_line_id.id)
        invoice_purchase.sort()
        stock_move_purchase.sort()
        if invoice_purchase == stock_move_purchase:
            return True
        else:
            return False

    # 去除需要分摊开票的总金额和采购订单的总金额
    @api.multi
    def _get_share_invoice_line(self, values, type):
        if type == "by_value":
            share_amount = 0.0
            be_shared_amount = 0.0
            for invoice_line in values:
                if invoice_line.purchase_line_id and invoice_line.product_id.type != "service":
                    share_amount += invoice_line.price_subtotal
                else:
                    be_shared_amount += invoice_line.price_subtotal

            return share_amount, be_shared_amount
        else:
            be_shared_amount = 0.0
            share_count = 0.0
            for invoice_line in values:
                if invoice_line.purchase_line_id and invoice_line.product_id.type != "service":
                    share_count += invoice_line.quantity
                else:
                    be_shared_amount += invoice_line.price_subtotal
            return share_count, be_shared_amount

    @api.multi
    def action_balance(self):
        flg = False
        if self._check_consistent(self.invoice_line_ids, self.stock_move_ids):
            if self.share_type == "by_value": # 按金额分摊
                # 判断是否有没挂订单的开票
                for invoice_line in self.invoice_line_ids:
                    if not invoice_line.purchase_line_id:
                        flg = True
                        break
                if flg:
                    purchase_share_obj, purchase_share_amount = self.share_by_value()
                    # 开始分摊并保存
                    for stock_move_line in self.stock_move_ids:
                        if stock_move_line.purchase_line_id:
                            value = {"cost_test": purchase_share_obj[stock_move_line.purchase_line_id.id], "amount": purchase_share_amount[stock_move_line.purchase_line_id.id], "handle_flg": True}
                            stock_move_line.update(value)
                else:  # 开票行和库存移动对应，直接将开票的金额和单价保存在库存移动中
                    # 保存成本
                    for invoice_line in self.invoice_line_ids:
                        for stock_move in self.stock_move_ids:
                            if invoice_line.purchase_line_id.id == stock_move.purchase_line_id.id:
                                # 计算税
                                amount = 0.0
                                for invoice_line_tax_id in invoice_line.invoice_line_tax_ids:
                                    amount += invoice_line_tax_id.amount
                                value = {"cost_test": invoice_line.price_subtotal / invoice_line.quantity,
                                         "amount": invoice_line.price_subtotal,
                                         "handle_flg": True}
                                stock_move.update(value)
            else: # 按数量分摊
                # 判断是否有没挂订单的开票
                for invoice_line in self.invoice_line_ids:
                    if not invoice_line.purchase_line_id:
                        flg = True
                        break
                if flg: # 如果有未挂订单的开票信息，则计算分摊
                    purchase_share_obj, purchase_share_amount = self.share_by_count()
                    # 开始分摊并保存
                    for stock_move_line in self.stock_move_ids:
                        if stock_move_line.purchase_line_id:
                            value = {"cost_test": purchase_share_obj[stock_move_line.purchase_line_id.id],
                                     "amount": purchase_share_amount[stock_move_line.purchase_line_id.id],
                                     "handle_flg": True}
                            stock_move_line.update(value)
                else:  # 开票行和库存移动对应，直接将开票的金额和单价保存在库存移动中
                    for invoice_line in self.invoice_line_ids:
                        for stock_move in self.stock_move_ids:
                            if invoice_line.purchase_line_id.id == stock_move.purchase_line_id.id:
                                # 计算税
                                amount = 0.0
                                for invoice_line_tax_id in invoice_line.invoice_line_tax_ids:
                                    amount += invoice_line_tax_id.amount
                                value = {"cost_test": invoice_line.price_subtotal / invoice_line.quantity,  # 计算未税单价
                                         "amount": invoice_line.price_subtotal,  # 开票行的未税金额
                                         "handle_flg": True}
                                stock_move.update(value)
        else:
            raise ValidationError(_("选择的开票明细和入库明细不一致"))
        return True

    @api.multi
    def write(self, value):
        # 核算成本
        result = super(inventory_balance, self).write(value)
        self.action_balance()
        return result

    @api.model
    def create(self, value):
        value['code'] = self.env['ir.sequence'].next_by_code('inventory.balance') or 'New'
        result = super(inventory_balance, self).create(value)
        result.action_balance()
        return result

    @api.multi
    def button_balance(self):
        for stock in self.stock_move_ids:
            value_stock = {
                "cost": stock.cost_test,
                "account_type": "1",
                "handle_flg": True
            }
            stock.update(value_stock)
        for invoice_line in self.invoice_line_ids:
            invoice_line.update({"state": "balance"})
            invoice_line.invoice_id.update({"balance_flg": True})

        self.write({"state": "balance", "balance_date": datetime.datetime.now()})
        return True

    @api.multi
    def button_cancel(self):
        if self.state == "account":
            raise ValidationError(_("单据已记账，不允许取消"))

        for stock in self.stock_move_ids:
            value_stock = {
                "cost": None,
                "account_type": "0",
                "handle_flg": False
            }
            stock.update(value_stock)
        for invoice_line in self.invoice_line_ids:
            invoice_line.update({"state": "unbalance"})
            invoice_line.invoice_id.update({"balance_flg": False})

        self.write({"state": "draft"})

        return True

    @api.multi
    def unlink(self):
        unlink_flg = False
        for balance in self:
            if balance.state != "draft":
                unlink_flg = True
        if not unlink_flg:
            return super(inventory_balance, self).unlink()
        else:
            raise ValidationError(_("只有草稿单据才可以删除"))
