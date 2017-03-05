# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError
import datetime


class DACostInputStockMove(models.Model):
    _inherit = "stock.move"

    input_id = fields.Many2one("cost.input", string=u'成本录入单')


class DACostInput(models.Model):
    _name = "cost.input"

    @api.model
    def _default_date_from(self):
        today = datetime.datetime.now()
        return today.replace(day=1).strftime("%Y-%m-%d")

    @api.model
    def _default_date_to(self):
        if datetime.datetime.now().month == 12:
            target = datetime.datetime.now().replace(year=datetime.datetime.now().year + 1, month=1, day=1) - \
                     datetime.timedelta(days=1)
        else:
            target = datetime.datetime.now().replace(month=datetime.datetime.now().month + 1, day=1) - \
                     datetime.timedelta(days=1)
        return target.strftime("%Y-%m-%d")

    @api.model
    def _default_stock_type(self):
        if self.env['type.account.relation'].search([('purchase_in', '=', 'other_in')], limit=1):
            return self.env['type.account.relation'].search([('purchase_in', '=', 'other_in')], limit=1)
        else:
            return False

    name = fields.Char(string=u'描述', required=True, copy=False)
    order_date = fields.Date(string=u'单据日期', copy=False, default=fields.Date.context_today)
    line_ids = fields.One2many("cost.input.line", "input_id", string=u'明细')
    date_from = fields.Date(string=u'起始日期', default=_default_date_from, required=True)
    date_to = fields.Date(string=u'结束日期', default=_default_date_to, required=True)
    confirm_date = fields.Date(string=u'验证时间', readonly=True)
    stock_in_type = fields.Many2one("type.account.relation", required=True, domain="[('purchase_in','=','other_in')]",
                                    default=_default_stock_type)
    state = fields.Selection([("draft", u'草稿'), ("confirmed", u'已验证'), ("cancel", u'取消')],
                             required=True, default="draft", string=u'状态')
    confirmed = fields.Boolean(string=u'已更新成本', default=False)
    confirm_move = fields.One2many("stock.move", "input_id", string=u'更新的库存单')

    @api.multi
    def view_pickings(self):
        picking_ids = []
        for move in self.confirm_move:
            if move.picking_id.id not in picking_ids:
                picking_ids.append(move.picking_id.id)
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('stock.action_picking_tree_all')
        form_view_id = imd.xmlid_to_res_id('stock.view_picking_form')
        tree_view_id = imd.xmlid_to_res_id('stock.vpicktree')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[tree_view_id, 'tree'], [form_view_id, 'form']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            'domain': "[('id', 'in', %s)]" % picking_ids
        }
        return result

    @api.multi
    def action_confirm(self):
        moves = self.env['stock.move'].search([("send_receive_type", '=', self.stock_in_type.id),
                                               ("picking_id.order_date", ">=", self.date_from),
                                               ("picking_id.order_date", "<=", self.date_to),
                                               ("product_id", "in", map(lambda x: x.product_id.id, self.line_ids))])
        costs = dict(map(lambda x: (x.product_id.id, x.cost), self.line_ids))
        for move in moves:
            if move.product_id.id in costs.keys():
                move.write({'input_id': self.id, "cost": costs[move.product_id.id]})
        return self.write({'state': "confirmed", 'confirmed': True, "confirm_date": datetime.datetime.utcnow()})

    @api.multi
    def action_cancel(self):
        return self.write({'state': "cancel"})

    @api.multi
    def action_draft(self):
        return self.write({"state": "draft"})

    @api.model
    def unlink(self):
        if self.confirmed:
            raise UserError(_("已更新过成本不可删除"))
        else:
            return super(DACostInput, self).unlink()


class DACostInputLine(models.Model):
    _name = "cost.input.line"

    input_id = fields.Many2one("cost.input", string=u'成本录入', required=True)
    product_id = fields.Many2one("product.product", string=u'产品', required=True, domain="[('type','=','consu')]")
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    cost = fields.Monetary(string=u'成本')