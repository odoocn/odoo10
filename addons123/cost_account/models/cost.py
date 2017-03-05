#coding:utf-8
from odoo import api, fields, models,_
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_utils

class StockMove(models.Model):
    _inherit = "stock.move"
    finish_id=fields.Many2one('finish.report')

class StockScrap(models.Model):
    _inherit = "stock.scrap"
    finish_id=fields.Many2one('finish.report')
#制造订单
class MrpProduction(models.Model):
    _inherit='mrp.production'

    cost_center_id=fields.Many2one('cost.center',string='成本中心')

#成本中心
class cost_center(models.Model):
    _name='cost.center'

    name=fields.Char(u'名称')
    department_id=fields.Many2one('hr.department',string='部门')
    is_active=fields.Boolean(u'是否停用',default=False)

#公用材料分配
class Common_material_distribution(models.Model):
    _name='material.distribution'
    _rec_name='cost_center_id'
    cost_center_id=fields.Many2one('cost.center',string='成本中心',required=True)
    type=fields.Selection([('1','按产品产量'),('2','按实际工时'),('3','按定额工时'),('4','按产品权重')],string='分配方式')
    allocation_id=fields.One2many('weight.allocation','material_id',string='分配比例')

    _sql_constraints = [
        ('name_uniq', 'unique (cost_center_id)', "该成本中心已设置!"),
    ]

    @api.onchange('type')
    def change_type(self):
        if self.allocation_id:
            self.allocation_id=''

#直接人工分配
class manual_distribution(models.Model):
    _name='manual.distribution'
    _rec_name='cost_center_id'
    cost_center_id=fields.Many2one('cost.center',string='成本中心',required=True)
    type=fields.Selection([('1','按产品产量'),('2','按实际工时'),('3','按定额工时'),('4','按产品权重')],string='分配方式')
    allocation_id=fields.One2many('weight.allocation','manual_id',string='分配比例')

    _sql_constraints = [
        ('name_uniq', 'unique (cost_center_id)', "该成本中心已设置!"),
    ]

    @api.onchange('type')
    def change_type(self):
        if self.allocation_id:
            self.allocation_id=''

#折旧费用分配
class expense_distribution(models.Model):
    _name='expense.distribution'
    _rec_name='cost_center_id'

    cost_center_id=fields.Many2one('cost.center',string='成本中心')
    type=fields.Selection([('1','按产品产量'),('2','按实际工时'),('3','按定额工时'),('4','按产品权重')],string='分配方式')
    allocation_id=fields.One2many('weight.allocation','expense_id',string='分配比例')

    _sql_constraints = [
        ('name_uniq', 'unique (cost_center_id)', "该成本中心已设置!"),
    ]

    @api.onchange('type')
    def change_type(self):
        if self.allocation_id:
            self.allocation_id=''
#废品费用分配
class waste_expense_distribution(models.Model):
    _name='waste.expense.distribution'
    _rec_name='cost_center_id'
    cost_center_id=fields.Many2one('cost.center',string='成本中心',required=True)
    type=fields.Selection([('1','按产品产量'),('2','按实际工时'),('3','按定额工时'),('4','按产品权重')],string='分配方式')
    allocation_id=fields.One2many('weight.allocation','waste_expense_distribution_id',string='分配比例')

    _sql_constraints = [
        ('name_uniq', 'unique (cost_center_id)', "该成本中心已设置!"),
    ]

    @api.onchange('type')
    def change_type(self):
        if self.allocation_id:
            self.allocation_id=''
#其他费用分配
class other_expense_distribution(models.Model):
    _name='other.expense.distribution'
    _rec_name='cost_center_id'
    cost_center_id=fields.Many2one('cost.center',string='成本中心',required=True)
    type=fields.Selection([('1','按产品产量'),('2','按实际工时'),('3','按定额工时'),('4','按产品权重')],string='分配方式')
    allocation_id=fields.One2many('weight.allocation','other_expense_distribution_id',string='分配比例')

    _sql_constraints = [
        ('name_uniq', 'unique (cost_center_id)', "该成本中心已设置!"),
    ]

    @api.onchange('type')
    def change_type(self):
        if self.allocation_id:
            self.allocation_id=''
#费用明细
class expense_lines(models.Model):
    _name='expense.lines'
    name=fields.Char(u'名称')

#在产品成本分配
class cost_distribution(models.Model):
    _name='cost.distribution'
    _rec_name='cost_center_id'
    cost_center_id=fields.Many2one('cost.center',string='成本中心',required=True)
    type=fields.Selection([('1','不计算产品'),('2','完工定额倒挤'),('3','按定额工时'),('4','按实际工时'),('5','只计算材料成本'),('6','产品约当产量'),('7','在产定额计算')],string='分配方式')
    allocation_id=fields.One2many('percent.allocation','cost_id',string='分配比例')

    _sql_constraints = [
        ('name_uniq', 'unique (cost_center_id)', "该成本中心已设置!"),
    ]

    @api.onchange('type')
    def change_type(self):
        if self.allocation_id:
            self.allocation_id=''

#约当系数分配
class percent_allocation(models.Model):
    _name='percent.allocation'
    name=fields.Char(u'成本中心',readonly=True)
    cost_id=fields.Many2one('cost.distribution',ondelete='cascade')
    product_id=fields.Many2one('product.product',string='产品')
    code=fields.Char(u'产品编号',readonly=True)
    h_percent=fields.Float(u'人工约当系数')
    c_percent=fields.Float(u'制造约当系数')
    m_percent=fields.Float(u'材料约当系数')

    @api.onchange('product_id')
    def code_add(self):
        self.code=self.product_id.id

    @api.model
    def create(self,val):
        obj=super(percent_allocation,self).create(val)
        obj.name=obj.cost_id.cost_center_id.name
        obj.code=obj.product_id.id
        return obj

#权重分配比
class weight_allocation(models.Model):
    _name='weight.allocation'

    name=fields.Char(u'成本中心',readonly=True)
    material_id=fields.Many2one('material.distribution',ondelete='cascade')
    manual_id=fields.Many2one('manual.distribution',ondelete='cascade')
    expense_id=fields.Many2one('expense.distribution',ondelete='cascade')
    product_id=fields.Many2one('product.product',string='产品',ondelete='cascade')
    waste_expense_distribution_id=fields.Many2one('waste.expense.distribution',ondelete='cascade')
    other_expense_distribution_id=fields.Many2one('other.expense.distribution',ondelete='cascade')
    code=fields.Char(u'产品编号',readonly=True)
    percent=fields.Float(u'权重系数')

    @api.onchange('product_id')
    def code_add(self):
        self.code=self.product_id.id

    @api.model
    def create(self,val):
        obj=super(weight_allocation,self).create(val)
        if obj.material_id:
            obj.name=obj.material_id.cost_center_id.name
        elif obj.manual_id:
            obj.name=obj.manual_id.cost_center_id.name
        elif obj.expense_id:
            obj.name=obj.expense_id.cost_center_id.name
        elif obj.waste_expense_distribution_id:
            obj.name=obj.waste_expense_distribution_id.cost_center_id.name
        elif obj.other_expense_distribution_id:
            obj.name=obj.other_expense_distribution_id.cost_center_id.name
        obj.code=obj.product_id.id
        return obj

#期初余额
class period_balance(models.Model):
    _name='period.balance'
    _rec_name='cost_center_id'
    cost_center_id=fields.Many2one('cost.center',string='成本中心',required=True)
    product_id=fields.Many2one('product.product',string='产品')
    bom=fields.Char(u'bom版本')
    number=fields.Float(u'数量')
    cai_expense=fields.Float(u'材料费用')
    ren_gong_expense=fields.Float(u'直接人工')
    zhi_zao_expense=fields.Float(u'制造费用')
    other_expense=fields.Float(u'其他费用')
    total_expense=fields.Float(u'总费用')
    total_cost=fields.Float(u'总成本')


    _sql_constraints = [
        ('name_uniq', 'unique (cost_center_id)', "该成本中心已设置!"),
    ]


#工时表
class time_sheet(models.Model):
    _name='time.sheet'
    _rec_name='cost_center_id'
    cost_center_id=fields.Many2one('cost.center',string='成本中心',required=True)
    product_id=fields.Many2one('product.product',string='产品')
    bom=fields.Char(u'bom版本')
    order_id=fields.Many2one('mrp.production',string='订单')
    actual_time=fields.Char(u'实际人工工时')
    quota_time=fields.Char(u'定额人工工时')
    start_date=fields.Date(u'期间开始')
    end_date=fields.Date(u'期间结束')

    # _sql_constraints = [
    #     ('name_uniq', 'unique (cost_center_id)', "该成本中心已设置!"),
    # ]

    @api.onchange('order_id')
    def get_data(self):
        if self.order_id:
            self.product_id=self.order_id.product_id.id
            self.bom=self.order_id.bom_id.type


#材料耗用
class Material_Consumption(models.Model):
    _name='material.consumption'
    _rec_name='cost_center_id'
    cost_center_id=fields.Many2one('cost.center',string='成本中心',required=True)
    product_id=fields.Many2one('product.product',string='产品')
    bom=fields.Char(u'bom版本')
    number=fields.Float(u'数量')
    # material=fields.fields.One2many('mrp.bom.line','material_id',string='材料')
    material=fields.Char(u'材料')
    order_id=fields.Many2one('mrp.production',string='订单')
    expense=fields.Float(u'金额')
    cost=fields.Float(u'成本')
    finish_report_id=fields.Many2one('finish.report')
    wast=fields.Float(u'报废数量')




    # @api.onchange('order_id')
    # def get_data(self):
    #     if self.order_id:
    #         self.product_id=self.order_id.product_id.id
    #         self.bom=self.order_id.bom_id.type
    #         self.material=self.order_id.bom_id.bom_line_ids.product_id.name
    #         self.number=self.order_id.product_qty


#公用材料填报
class public_material(models.Model):
    _name='public.material'
    cost_center_id=fields.Many2one('cost.center',string='成本中心',required=True)
    product_id=fields.Many2one('product.product',string='产品')
    number=fields.Float(u'数量')

#完工产品日报表
class finish_report(models.Model):
    _name='finish.report'
    _rec_name='cost_center_id'
    cost_center_id=fields.Many2one('cost.center',string='成本中心',required=True)
    product_id=fields.Many2one('product.product',string='产品',readonly=True)
    bom=fields.Char(u'bom版本',readonly=True)
    order_id=fields.Many2one('mrp.production',string='订单',required=True)
    complete_number=fields.Float(u'完成产量',readonly=True)
    waste=fields.Float(u'废品',readonly=True)
    net_production=fields.Float(u'净产量')
    in_production=fields.Float(u'入库量')
    start_date=fields.Date(u'期间开始')
    end_date=fields.Date(u'期间结束')
    # material_id=fields.One2many('material.consumption','finish_report_id')
    stock_move_id=fields.One2many('stock.move','finish_id')
    scrap_id=fields.One2many('stock.scrap','finish_id')


    _sql_constraints = [
        ('name_uniq', 'unique (cost_center_id)', "该成本中心已设置!"),
    ]


    @api.onchange('order_id')
    def get_data(self):
        if self.order_id:
            self.product_id=self.order_id.product_id.id
            self.bom=self.order_id.bom_id.type
            wast_num=complete_num=0
            for obj in self.order_id.move_finished_ids:
                complete_num+=obj.quantity_done
            for obj in self.order_id.scrap_ids:
                if obj.product_id==self.product_id:
                    wast_num+=obj.scrap_qty
            self.complete_number=complete_num
            self.waste=wast_num


    @api.model
    def create(self,val):
        obj=super(finish_report,self).create(val)
        if obj.order_id:
            obj.product_id=obj.order_id.product_id.id
            obj.bom=obj.order_id.bom_id.type
            wast_num=complete_num=0
            for pro in obj.order_id.move_finished_ids:
                complete_num+=pro.quantity_done
            for pro in obj.order_id.scrap_ids:
                if pro.product_id==obj.product_id:
                    wast_num+=pro.scrap_qty

            obj.complete_number=complete_num
            obj.waste=wast_num
            for moves in obj.order_id.move_raw_ids:
                moves.write({'finish_id':obj.id})
            for scraps in obj.order_id.scrap_ids:
                scraps.write({'finish_id':obj.id})
        return obj

    @api.multi
    def write(self, vals):
        if vals.get('order_id'):
            for moves in self.order_id.move_raw_ids:
                moves.update({'finish_id':''})
            for scraps in self.order_id.scrap_ids:
                scraps.update({'finish_id':''})
            super(finish_report, self).write(vals)
            self.product_id=self.order_id.product_id.id
            self.bom=self.order_id.bom_id.type
            wast_num=complete_num=0
            for pro in self.order_id.move_finished_ids:
                complete_num+=pro.quantity_done
            for pro in self.order_id.scrap_ids:
                if pro.product_id==self.product_id:
                    wast_num+=pro.scrap_qty
            self.complete_number=complete_num
            self.waste=wast_num
            for moves in self.order_id.move_raw_ids:
                moves.update({'finish_id':self.id})
            for scraps in self.order_id.scrap_ids:
                scraps.update({'finish_id':self.id})
        return super(finish_report, self).write(vals)














    #         material_num=0
    #         for line in obj.order_id.move_raw_ids:
    #             for pro in obj.order_id.scrap_ids:
    #                 if pro.product_id==line.product_id:
    #                     material_num+=pro.scrap_qty
    #             material=self.env['material.consumption'].create({
    #                 'finish_report_id':self.id,
    #                 'cost_center_id':obj.cost_center_id.id,
    #                 'order_id':obj.order_id.id,
    #                 'product_id':obj.order_id.product_id.id,
    #                 'bom':obj.order_id.bom_id.type,
    #                 'material':line.product_id.name,
    #                 'number':line.quantity_done,
    #                 'wast':material_num
    #             })
    #             material.update({'finish_report_id':obj})
    #     return obj
    #
    # @api.multi
    # def write(self, vals):
    #     if vals.get('cost_center_id'):
    #         self.material_id.update({'cost_center_id':vals.get('cost_center_id')})
    #     if vals.get('order_id'):
    #         super(finish_report, self).write(vals)
    #
    #         material_num=0
    #         for line in self.order_id.move_raw_ids:
    #             for pro in self.order_id.scrap_ids:
    #                 if pro.product_id==line.product_id:
    #                     material_num+=pro.scrap_qty
    #             self.material_id.update({
    #                 'finish_report_id': self,
    #                 'order_id': self.order_id.id,
    #                 'product_id': self.order_id.product_id.id,
    #                 'bom': self.order_id.bom_id.type,
    #                 'material':line.product_id.name,
    #                 'number':line.quantity_done,
    #                 'wast':material_num
    #             })
    #
    #         self.product_id=self.order_id.product_id.id
    #         self.bom=self.order_id.bom_id.type
    #         wast_num=complete_num=0
    #         for pro in self.order_id.move_finished_ids:
    #             complete_num+=pro.quantity_done
    #         for pro in self.order_id.scrap_ids:
    #             if pro.product_id==self.product_id:
    #                 wast_num+=pro.scrap_qty
    #         self.complete_number=complete_num
    #         self.waste=wast_num
    #     return super(finish_report, self).write(vals)
    #
    #
    # @api.multi
    # def unlink(self):
    #     for objs in self:
    #         for obj in objs.material_id:
    #             obj.unlink()
    #     return super(finish_report, self).unlink()
    #
    #
    #
