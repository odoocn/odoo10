# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import datetime


class inventory_account(models.Model):
    _name = "inventory.account"
    _rec_name = "code"

    account_date = fields.Date(u'记账日期')
    code = fields.Char(u'编码')
    stock_move_ids = fields.Many2many('stock.move', string=u'出入库明细')
    state = fields.Selection([('draft', '草稿'), ('account', '已记账')], default="draft", string=u'状态')

    @api.model
    def create(self, values):
        values['code'] = self.env['ir.sequence'].next_by_code('inventory.account') or 'New'

        return super(inventory_account, self).create(values)

    @api.multi
    def button_account(self):
        self._account_month(sorted(self.stock_move_ids))
        result = {
            "account_date": datetime.datetime.now(),
            "state": "account",
        }
        self.update(result)
        return True

    @api.multi
    def _account_month(self, values):
        all_product_ids = []
        moving_product_ids = []
        # 取得产品ID列表
        for stock_move in values:
            if stock_move.product_tmpl_id.inventory_method == "all":
                all_product_ids.append(stock_move.product_id.id)
            else:
                moving_product_ids.append(stock_move.product_id.id)
        all_product_ids = list(set(all_product_ids))
        moving_product_ids = list(set(moving_product_ids))
        # 全月一次加权平均法
        all_out_cost = {}  # 全月平均法算出产品的出库成本
        all_current_stock = {}  # 本次结余库存
        all_current_amount = {}  # 本次结余金额
        for product_id in all_product_ids:
            in_count = 0.0  # 入库数量
            in_amount = 0.0  # 入库总额
            out_count = 0.0  # 出库数量
            for stock_move in values:
                if stock_move.product_id.id == product_id:  # 判断同一产品
                    if stock_move.send_receive_type.purchase_in in ("purchase_in", "other_in"):  # 判断库存移动是入库
                            in_count += stock_move.product_qty
                            if stock_move.account_type == "1":
                                in_amount += stock_move.amount
                            else:
                                in_amount += stock_move.product_qty * stock_move.price_unit
                    if stock_move.send_receive_type.purchase_in in ("sale_out", "other_out"):  # 出库
                        # 取得所有入库单数量和成本总额
                        out_count += stock_move.product_qty
            # 取得产品的上次结存信息
            inventory_cost = self.env['inventory.cost'].search([('product_id', '=', product_id)])
            if inventory_cost:
                current_amount = inventory_cost[0].current_amount
                stock = inventory_cost[0].stock
            else:
                current_amount = 0.0
                stock = 0.0
            # 出库成本计算公式：（入库总额+期初总额）/ 出库总数量
            out_cost = (in_amount + current_amount) / (in_count + stock)
            all_out_cost[product_id] = out_cost
            # 本次结存数量
            all_current_stock[product_id] = in_count + stock - out_count
            # 本次结余金额
            all_current_amount[product_id] = in_amount + current_amount - (out_count * out_cost)
            # 记录明细账
            self._all_create_detail_account(product_id, values, all_out_cost)
        # 将记账成本会写到记账历史表
        for product_id in all_product_ids:
            if all_current_stock[product_id]:
                current_cost = all_current_amount[product_id] / all_current_stock[product_id]
            else:
                current_cost = 0.0
            value = {
                "stock": all_current_stock[product_id],
                "current_cost": current_cost,
                "current_amount": all_current_amount[product_id],
                "product_id": product_id,
                "date": datetime.datetime.now(),
                "inventory_account_id": self.id
            }
            self.env['inventory.cost'].create(value)

        # 移动加权平均法
        for product_id in moving_product_ids:
            # 取得产品的上次结存信息
            inventory_cost = self.env['inventory.cost'].search([('product_id', '=', product_id)])
            if inventory_cost:
                current_stock = inventory_cost[0].stock
                current_amount = inventory_cost[0].current_amount
                current_cost = inventory_cost[0].current_cost
            else:
                current_stock = 0.0
                current_amount = 0.0
                current_cost = 0.0
            for stock_move in values:
                if stock_move.product_id.id == product_id:  # 判断同一产品
                    if stock_move.send_receive_type.purchase_in in ("purchase_in", "other_in"):  # 判断库存移动是入库
                        current_stock += stock_move.product_qty
                        if stock_move.account_type == "1":
                            stock_move_amount = stock_move.amount
                            stock_move_cost = stock_move.cost
                        else:
                            stock_move_amount = stock_move.product_qty * stock_move.price_unit
                            stock_move_cost = stock_move.price_unit
                        current_amount += stock_move_amount
                        # 保存产品明细账
                        if current_stock:
                            ballance_price = current_amount / current_stock
                        else:
                            ballance_price = 0.0
                        value = {
                            'account_date': datetime.datetime.now(),
                            'the_receipt': "",
                            'send_receive_type': stock_move.send_receive_type.id,
                            'in_qty': stock_move.product_qty,
                            'in_cost_price': stock_move_cost,
                            'in_cost_amount': stock_move_amount,
                            'balance_qty': current_stock,
                            'balance_price': ballance_price,
                            'balance_amount': current_amount,
                            'product_id': product_id,
                            'uom_id': stock_move.product_tmpl_id.uom_id.id,
                        }
                        self.env['product.detail.account'].create(value)
                        stock_move.update({"account_type": "2", "handle_flg": False})
                    if stock_move.send_receive_type.purchase_in in ("sale_out", "other_out"):  # 出库
                        current_stock -= stock_move.product_qty
                        current_amount -= current_cost * stock_move.product_qty
                        if current_stock:
                            ballance_price = current_amount / current_stock
                        else:
                            ballance_price = 0.0
                        value = {
                            'account_date': datetime.datetime.now(),
                            'the_receipt': "",
                            'send_receive_type': stock_move.send_receive_type.id,
                            'out_qty': stock_move.product_qty,
                            'out_cost_price': current_cost,
                            'out_cost_amount': stock_move.product_uom_qty * current_cost,
                            'balance_qty': current_stock,
                            'balance_price': ballance_price,
                            'balance_amount': current_amount,
                            'product_id': product_id,
                            'uom_id': stock_move.product_tmpl_id.uom_id.id,
                        }
                        self.env['product.detail.account'].create(value)
                        stock_move.update({"account_type": "2", "handle_flg": False, "cost": current_cost,})
                    current_cost = ballance_price
            # 计算成本，保存中间表
            value = {
                "stock": current_stock,
                "current_cost": ballance_price,
                "current_amount": current_amount,
                "product_id": product_id,
                "date": datetime.datetime.now(),
                "inventory_account_id": self.id
            }

            self.env['inventory.cost'].create(value)

        # 更新库存移动单据的状态，并更新出库移动单的出库成本
        for stock_move in values:
            if stock_move.product_id.id in all_product_ids:
                if stock_move.send_receive_type.purchase_in in ("sale_out", "other_out"):
                    value = {
                        "cost": all_out_cost[stock_move.product_id.id],
                        "account_type": "2",
                    }
                    stock_move.update(value)
                if stock_move.send_receive_type.purchase_in in ("purchase_in", "other_in"):
                    value = {
                        "account_type": "2",
                        "handle_flg": False
                    }
                    stock_move.update(value)

        return True

    # 全月一次加权平均法插入明细账
    @api.multi
    def _all_create_detail_account(self, product_id, values, all_out_cost):
        # 取得产品当前结存信息
        detail_account = self.env['inventory.cost'].search([('product_id', '=', product_id)])
        if detail_account:
            current_amount = detail_account[0].current_amount
            stock = detail_account[0].stock
        else:
            current_amount = 0.0
            stock = 0.0
        for stock_move in values:
            # 判断库存移动的产品是全月一次加权平均法记账
            if stock_move.product_id.id == product_id:
                # 判断库存移动是入库，则计算结存成本 = （结存金额 + 入库金额）/ （结存数量 + 入库数量）
                if stock_move.send_receive_type.purchase_in in ("purchase_in", "other_in"):
                    if stock_move.account_type == "1":
                        stock_move_amount = stock_move.amount
                        stock_move_cost = stock_move.cost
                    else:
                        stock_move_amount = stock_move.product_qty * stock_move.price_unit
                        stock_move_cost = stock_move.price_unit
                    current_amount += stock_move_amount
                    stock += stock_move.product_qty
                    if stock:
                        ballance_price = current_amount / stock
                    else:
                        ballance_price = 0.0
                    value = {
                        'account_date': datetime.datetime.now(),
                        'the_receipt': "",
                        'send_receive_type': stock_move.send_receive_type.id,
                        'in_qty': stock_move.product_qty,
                        'in_cost_price': stock_move_cost,
                        'in_cost_amount': stock_move_amount,
                        'balance_qty': stock,
                        'balance_price': ballance_price,
                        'balance_amount': current_amount,
                        'product_id': product_id,
                        'uom_id': stock_move.product_tmpl_id.uom_id.id,
                    }
                    self.env['product.detail.account'].create(value)
                if stock_move.send_receive_type.purchase_in in ("sale_out", "other_out"):  # 出库
                    current_amount -= stock_move.product_uom_qty * all_out_cost[product_id]
                    stock -= stock_move.product_qty
                    # 本次结余数量
                    if stock:
                        ballance_price = current_amount / stock
                    else:
                        ballance_price = 0.0
                    value = {
                        'account_date': datetime.datetime.now(),
                        'the_receipt': "",
                        'send_receive_type': stock_move.send_receive_type.id,
                        'out_qty': stock_move.product_qty,
                        'out_cost_price': all_out_cost[product_id],
                        'out_cost_amount': stock_move.product_uom_qty * all_out_cost[product_id],
                        'balance_qty': stock,
                        'balance_price': ballance_price,
                        'balance_amount': current_amount,
                        'product_id': product_id,
                        'uom_id': stock_move.product_tmpl_id.uom_id.id,
                    }
                    self.env['product.detail.account'].create(value)


class inventory_cost(models.Model):
    _name = "inventory.cost"
    _order = "id desc"

    stock = fields.Float(u"当前库存", digits=(16, 2))
    current_cost = fields.Float(u'结存单价', digits=(16, 4))
    current_amount = fields.Float(u'结存金额', digits=(16, 4))
    product_id = fields.Many2one("product.product", string=u'产品')
    date = fields.Date(u'记账日期')
    inventory_account_id = fields.Many2one("inventory.account", string=u'记账单')
    #---------------mlp
    is_active=fields.Boolean(u'是否期初',default=True)
    change_date=fields.Date(u'调整时间')


class product_detail_account(models.Model):
    _name = "product.detail.account"
    _description = u'明细账'
    _order = "product_id, id desc"

    account_date = fields.Date(u'记账日')
    the_receipt = fields.Char(u'凭证摘要')
    send_receive_type = fields.Many2one('type.account.relation', u'收发类型')
    in_qty = fields.Float(u'入库数量', digits=(16,4))
    in_cost_price = fields.Float(u'入库单价', digits=(16,4))
    in_cost_amount = fields.Float(u'入库总额', digits=(16,4))
    out_qty = fields.Float(u'出库数量', digits=(16, 4))
    out_cost_price = fields.Float(u'出库单价', digits=(16, 4))
    out_cost_amount = fields.Float(u'出库总额', digits=(16, 4))
    balance_qty = fields.Float(u'结存数量', digits=(16,4))
    balance_price = fields.Float(u'结存单价', digits=(16,4))
    balance_amount = fields.Float(u'结存成本', digits=(16,4))
    product_id = fields.Many2one("product.product", u"存货")
    uom_id = fields.Many2one('product.uom', u'计量单位')
    #---------------mlp
    is_active=fields.Boolean(u'是否期初',default=True)
    change_date=fields.Date(u'调整时间')
