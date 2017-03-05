# -*- coding: utf-8 -*-

"""
合同类型、合同标签、合同概要、合同标的、变动历史、条款、大事记
"""

from odoo import models, fields, api, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp
import time


class CmType(models.Model):
    _name = 'cm.type'
    _description = u'合同分类'

    name = fields.Char(string=u'分类名称', required=True)
    kind = fields.Selection([('AR', '应收'), ('AP', '应付')], string=u'业务类型', required=True)
    order = fields.Boolean(string=u'订单')
    invoice = fields.Boolean(string=u'发票或账单')
    note = fields.Text(string=u'描述')


# 合同标签
class CmCategory(models.Model):
    _name = 'cm.category'
    _description = u'合同标签'
    _log_access = False  # 精简字段

    name = fields.Char(string=u'标签', required=True)
    # contract_ids = fields.Many2many('cm.contract', 'category_id', string=u'合同')
    color = fields.Integer(string=u'颜色索引')
    active = fields.Boolean(string=u'有效', default=True)


# 合同标的档案
class CmProduct(models.Model):
    _name = 'cm.product'
    _description = u'合同标的档案'
    _log_access = False  # 精简字段

    name = fields.Char(string=u'标的名称', required=True)
    active = fields.Boolean(string=u'有效', default=True)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    contract_id = fields.Many2one('cm.contract', string=u'挂钩合同')


# 合同主表
class CmContract(models.Model):
    _name = 'cm.contract'
    _description = u'合同主表'

    name = fields.Char(string=u'合同名称', required=True)
    re_id = fields.Integer(string=u'原始合同id')
    code = fields.Char(string=u'合同编号')
    type = fields.Many2one('cm.type', string=u'合同分类')
    kind = fields.Selection([('AR', '应收'), ('AP', '应付')], string=u'业务类型', required=True)
    property = fields.Selection([('FA', '框架协议'), ('CC', '合同')], string=u'合同类型')
    category_id = fields.Many2many('cm.category', string=u'标签')

    partner_id = fields.Many2one('res.partner', string=u'对方单位', required=True)
    child_id = fields.Char(string=u'联系人', required=True)
    partner_phone = fields.Char(string=u'对方电话')
    partner_email = fields.Char(string=u'Email')
    partner_address = fields.Char(string=u'对方地址')
    show = fields.Boolean(string=u'是否显示', default=True)
    user_id = fields.Many2one('res.users', string=u'业务员', required=True)
    company_phone = fields.Char(string=u'公司电话')
    company_email = fields.Char(string=u'Email')
    company_address = fields.Char(string=u'公司地址')
    # currency_id = fields.Many2one("res.currency", string='货币', readonly=True,required=True)
    amount_total = fields.Float(string=u'合同总金额')
    amount_tax = fields.Float(string=u'合同税金')
    changing = fields.Boolean(default=False, string=u'是否申请了变更', copy=False)
    copy_to = fields.Integer(u'修订版', default=None)
    copy_from = fields.Integer(u'初版', default=None)
    sign_date = fields.Date(string=u'签约时间')
    template_id = fields.Many2one(
        'mail.template', 'Use template', index=True)
    state = fields.Selection([
        ('draft', '草稿'),
        ('effective', '生效中'),
        ('suspend', '暂停'),
        ('done', '已完成'),
        ('termination', '终止'),
        ('cancel', '已取消')], string=u'类型', readonly=True, copy=False, index=True,
        default='draft')
    start_date = fields.Date(string=u'开始日期')
    end_date = fields.Date(string=u'结束日期')
    active = fields.Boolean(string=u'归档', default=True, help=U"合同归档")
    note = fields.Text(string=u'描述')

    def send_contract(self):
        self.state = 'done'
        return self.state

    def confirm_contract(self):
        self.state = 'effective'
        return self.state

    contract_object = fields.One2many('cm.contract.object', 'contract_id', string=u'合同标的', copy=True)
    contract_pay = fields.One2many('cm.contract.pay', 'contract_id', string=u'收付款条款', copy=True)
    contract_terms = fields.One2many('cm.contract.terms', 'contract_id', string=u'条款大事记', copy=True)
    contract_version = fields.One2many('cm.contract.version', 'contract_id', string=u'版本', copy=True)

    @api.multi
    def change_contract(self):
        new = self.copy()
        new.copy_from = self.id
        self.re_id = self.id
        new.re_id = self.id
        new.show = False
        self.changing = True
        self.copy_to = new.id

        self.env['cm.eco'].create(
            {'name': self.name + u'变更',
             'state': 'draft',
             'contract_id': self.id,
             'new_contract_id': new.id,
             })
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('a_contract.cm_contract_update_action')
        form_view_id = imd.xmlid_to_res_id('a_contract.cm_contract_update_from')

        result = {
            'name': action.name,
            'view_type': 'form',
            'view_mode': 'form',
            'type': action.type,
            'view_id': form_view_id,
            'target': action.target,
            'res_model': action.res_model,
            'res_id': new.id
        }
        return result

    @api.multi
    def create_sale(self):
        order = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            # 'contact_id': self.child_id,
            # 'partner_invoice_id': self.partner_id.id,#xuyaogai
            # 'partner_shipping_id': self.partner_address,
            # 'project_id': "",
            'contract_id': self.id,
            'order_name': self.name,
            'order_code': self.code,
            'data_from': time.strftime('%Y-%m-%d', time.localtime(time.time())),
            'date_order': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
            # 'pricelist_id':'1' ,
            'name': u'新建',
            # 'picking_policy':
            # 'warehouse_id':
        })

        for bom in self.contract_object:
            self.env['sale.order.line'].create({
                'order_id': order.id,
                'product_id': bom.product_id.id,
                'name': bom.name,  # 说明
                'product_uom_qty': bom.product_qty,  # 数量
                'price_unit': bom.price_unit,  # 单价
                'tax_id': [(6, 0, bom.tax_id.ids)],  # 税金
                # product_uom
            })

        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('sale.action_quotations')
        form_view_id = imd.xmlid_to_res_id('sale.view_order_form')
        result = {
            'name': action.name,
            'view_type': 'form',
            'view_mode': 'form',
            'type': action.type,
            'view_id': form_view_id,
            'res_model': action.res_model,
            'res_id': order.id
        }
        return result

    @api.multi
    def create_sale_template(self):
        # values = self.env['mail.compose.message'].generate_email_for_composer(self.template_id.id, self.ids[0])
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        # try:
        #     template_id = ir_model_data.get_object_reference('a_contract', 'email_template_edi_sale')[1]
        # except ValueError:
        #     template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('a_contract', 'email_compose_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'cm.contract',
            'default_res_id': self.ids[0],
            'default_use_template': bool(self.template_id.id),
            'default_template_id': self.template_id.id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def cancel_mail_action(self):
        # TDE/ ???
        return self.send_mail()

    @api.multi
    def changing_contract(self):
        copy = self.env['cm.contract'].search([('copy_from', '=', self.id)])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('a_contract.cm_contract_update_action')
        form_view_id = imd.xmlid_to_res_id('a_contract.cm_contract_update_from')

        result = {
            'name': action.name,
            'view_type': 'form',
            'view_mode': 'form',
            'type': action.type,
            'view_id': form_view_id,
            'target': action.target,
            'res_model': action.res_model,
            'res_id': copy.id
        }
        return result


# 合同标的
class CmContractObject(models.Model):
    _name = 'cm.contract.object'
    _description = u'合同标的'

    contract_id = fields.Many2one('cm.contract', string=u'合同参考', ondelete='cascade')
    product_id = fields.Many2one('product.product', string=u'标的物')
    product_tmpl_id = fields.Many2one(
        'product.template', u'标的物',
        domain="[('type', 'in', ['product', 'consu'])]")
    name = fields.Text(string=u'说明')
    product_qty = fields.Float(string=u'数量', default=0.00)
    price_unit = fields.Float(string=u'单价', default=0.00)
    rounding = fields.Float(
        'Rounding Precision', default=0.01, digits=0,
        help="The computed quantity will be a multiple of this value. "
             "Use 1.0 for a Unit of Measure that cannot be further split, such as a piece.")
    tax_id = fields.Many2many('account.tax', string=u'税')
    price_tax = fields.Monetary(compute='_compute_amount', string=u'税金', readonly=True, store=True)
    price_subtotal = fields.Monetary(compute='_compute_amount', string=u'无税金额', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string=u'含税金额', readonly=True, store=True)
    currency_id = fields.Many2one('res.currency', compute='_compute_currency', store=True, string="Currency")
    company_id = fields.Many2one('res.company', string='Company', store=True, readonly=True,
                                 default=lambda self: self.env.user.company_id)
    price_total_2 = fields.Float(string=u'总价', digits=dp.get_precision('Product Price'))

    @api.one
    @api.depends('company_id')
    def _compute_currency(self):
        self.currency_id = self.company_id.currency_id or self.env.user.company_id.currency_id

    @api.depends('product_qty', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        计算总计.
        """
        for line in self:
            # price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(line.price_unit, line.currency_id, line.product_qty,
                                            product=line.product_id, partner=line.contract_id.partner_id)
            one_price = 0
            if line.product_qty != 0:
                one_price = '%.2f' % (float(line.price_total_2) / line.product_qty)
            if float(one_price) == line.price_unit:
                line.update({
                    'price_tax': taxes['total_included'] - taxes['total_excluded'],
                    'price_total': float(line.price_total_2),
                    'price_subtotal': taxes['total_excluded'] + float(line.price_total_2) - taxes['total_included'],
                })
            else:
                line.update({
                    'price_tax': taxes['total_included'] - taxes['total_excluded'],
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                })


# 合同信息变更
class CmEco(models.Model):
    _name = 'cm.eco'
    _description = u'合同信息变更'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(u'信息变更')
    note = fields.Text(u'备注')
    state = fields.Selection([
        ('draft', '草稿'),
        ('confirmed', '生效')], string=u'状态', readonly=True, copy=False, index=True, track_visibility='onchange',
        default='draft')
    contract_id = fields.Many2one('cm.contract', u'合同', ondelete='cascade')
    contract_id_done = fields.Many2one('cm.contract', u'合同', ondelete='cascade')
    new_contract_id = fields.Many2one('cm.contract', u'新的合同', ondelete='cascade')
    last_contract_id = fields.Many2one('cm.contract', string=u'上版本合同', ondelete='cascade')
    contract_change_obj = fields.One2many('cm.eco.obj.change', 'eco_id', u'合同标的变更',
                                          compute='_compute_obj_change_ids', store=True)
    contract_change_pay = fields.One2many(u'变更后的收付款')

    @api.multi
    def confirm_change(self):
        self.state = 'confirmed'
        self.contract_id.changing = False
        self.last_contract_id = self.contract_id.id
        self.new_contract_id.states = 'effective'
        self.contract_id.show = False
        self.new_contract_id.show = True
        order = self.env['sale.order'].search([('contract_id', '=', self.contract_id.id)])
        order.write({'contract_id': self.new_contract_id.id})

    @api.depends('contract_id.contract_object', 'new_contract_id.contract_object')
    def _compute_obj_change_ids(self):
        new_obj_commands = []
        old_obj_lines = dict(
            (line.product_id, line) for line in self.contract_id.contract_object)
        if self.new_contract_id and self.contract_id:
            for line in self.new_contract_id.contract_object:
                key = line.product_id
                old_line = old_obj_lines.pop(key, None)
                if old_line and (tools.float_compare(old_line.product_qty, line.product_qty,
                                                     old_line.rounding) != 0 or tools.float_compare(old_line.price_unit,
                                                                                                    line.price_unit,
                                                                                                    old_line.rounding) != 0):
                    new_obj_commands += [(0, 0, {
                        'change_type': 'update',
                        'product_id': line.product_id.id,
                        'new_product_price': line.price_unit,
                        'old_product_price': old_line.price_unit,
                        'new_product_qty': line.product_qty,
                        'old_product_qty': old_line.product_qty})]

                elif not old_line:
                    new_obj_commands += [(0, 0, {
                        'change_type': 'add',
                        'product_id': line.product_id.id,
                        'new_product_qty': line.product_qty,
                        'new_product_price': line.price_unit
                    })]
            for key, old_line in old_obj_lines.iteritems():
                new_obj_commands += [(0, 0, {
                    'change_type': 'remove',
                    'product_id': old_line.product_id.id,
                    'old_product_qty': old_line.product_qty,
                    'old_product_price': old_line.price_unit,
                })]
        self.contract_change_obj = new_obj_commands

    @api.depends('contract_id.contract_pay', 'new_contract_id.contract_pay')
    def _compute_pay_change_ids(self):
        new_obj_commands = []
        old_obj_lines = dict((line.product_id, line) for line in self.contract_id.contract_pay)
        if self.new_contract_id and self.contract_id:
            for line in self.new_contract_id.contract_pay:
                key = line.product_id
                old_line = old_obj_lines.pop(key, None)


class CmEcoObjChange(models.Model):
    _name = 'cm.eco.obj.change'
    _description = u'修改合同标的'

    eco_id = fields.Many2one('cm.eco', 'Engineering Change', ondelete='cascade', required=True)
    change_type = fields.Selection([('add', '增加'), ('remove', '删除'), ('update', '修改')],
                                   string=u'类型', required=True)
    product_id = fields.Many2one('product.product', u'标的', required=True)
    old_product_qty = fields.Float(u'原始数量', default=0)
    new_product_qty = fields.Float(u'更新后数量', default=0)
    upd_product_qty = fields.Float(u'更新的数量', compute='_compute_upd_product_qty', store=True)
    old_product_price = fields.Float(u'原始价格', default=0)
    new_product_price = fields.Float(u'更新后价格', default=0)
    upd_product_price = fields.Float(u'更新的价格', compute='_compute_upd_product_price', store=True)

    @api.depends('new_product_qty', 'old_product_qty')
    def _compute_upd_product_qty(self):
        for qty in self:
            qty.upd_product_qty = qty.new_product_qty - qty.old_product_qty

    @api.depends('old_product_price', 'new_product_price')
    def _compute_upd_product_price(self):
        for price in self:
            price.upd_product_price = price.new_product_price - price.old_product_price


# 合同收付款条款
class CmContractPay(models.Model):
    _name = 'cm.contract.pay'
    _description = u'收付款条款'

    contract_id = fields.Many2one('cm.contract', string=u'合同参考', ondelete='cascade')
    # eco_id = fields.Many2one('cm.eco', string=u'收付款变更')
    name = fields.Char(string=u'付款说明')
    pay_ratio = fields.Float(string=u'付款比例')
    pay_currency = fields.Float(string=u'金额')
    pay_date = fields.Date(string=u'付款时间')
    note = fields.Text(string=u'描述')


# 合同条款/大事记
class CmContractTerms(models.Model):
    _name = 'cm.contract.terms'
    _description = u'条款/大事记'

    contract_id = fields.Many2one('cm.contract', string=u'合同参考', ondelete='cascade')
    name = fields.Char(string=u'标题')
    note = fields.Text(string=u'详细')


# 合同版本
class CmContractVersion(models.Model):
    _name = 'cm.contract.version'
    _description = u'文件列表'

    contract_id = fields.Many2one('cm.contract', string=u'合同参考', ondelete='cascade')
    name = fields.Char(string=u'版本说明')
    note = fields.Text(string=u'详细记录')
    attachment = fields.Binary(u'附件', attachment=True)
