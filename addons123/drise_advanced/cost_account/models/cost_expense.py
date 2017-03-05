#coding:utf-8
from odoo import api, fields, models,_
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_utils


#人工费用
class labor_cost(models.Model):
    _name='labor.cost'
    _rec_name='cost_center_id'
    cost_center_id=fields.Many2one('cost.center',string='成本中心',required=True)
    labor_expense=fields.Float(u'直接人工费用')
    manage_expense=fields.Float(u'管理人员工资')
    start_date=fields.Date(u'期间开始')
    end_date=fields.Date(u'期间结束')


    _sql_constraints = [
        ('name_uniq', 'unique (cost_center_id)', "该成本中心已设置!"),
    ]

#折旧费用
class Depreciation_expense(models.Model):
    _name='depreciation.expense'
    _rec_name='cost_center_id'
    cost_center_id=fields.Many2one('cost.center',string='成本中心',required=True)
    old_expense=fields.Float(u'折旧费用')
    start_date=fields.Date(u'期间开始')
    end_date=fields.Date(u'期间结束')


    _sql_constraints = [
        ('name_uniq', 'unique (cost_center_id)', "该成本中心已设置!"),
    ]

#废品费用
class factory_expenses(models.Model):
    _name='waste.expense'
    _rec_name='cost_center_id'
    cost_center_id=fields.Many2one('cost.center',string='成本中心',required=True)
    order_id=fields.Many2one('mrp.production',string='订单',required=True)
    product_id=fields.Many2one('product.product',string='产品')
    number=fields.Integer(u'数量')
    expense=fields.Float(u'金额')
    start_date=fields.Date(u'期间开始')
    end_date=fields.Date(u'期间结束')


    _sql_constraints = [
        ('name_uniq', 'unique (cost_center_id)', "该成本中心已设置!"),
    ]

    @api.onchange('order_id','product_id')
    def get_number(self):
        objs=self.env['stock.scrap'].search([('product_id','=',self.product_id.id),('production_id','=',self.order_id.id)])
        for obj in objs:
            self.number +=obj.scrap_qty
        self.expense=self.product_id.list_price
#其他费用
class other_expense(models.Model):
    _name='other.expense'
    _rec_name='cost_center_id'
    cost_center_id=fields.Many2one('cost.center',string='成本中心',required=True)
    # product_id=fields.Many2one('product.product',string='产品')
    bom=fields.Char(u'bom版本')
    order_id=fields.Char(u'订单号')
    expense_name=fields.Char(u'费用名称')
    expense=fields.Float(u'费用金额')
    start_date=fields.Date(u'期间开始')
    end_date=fields.Date(u'期间结束')


    _sql_constraints = [
        ('name_uniq', 'unique (cost_center_id)', "该成本中心已设置!"),
    ]
