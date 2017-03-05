# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import logging
import datetime
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)


class workflow_sale(models.Model):
    _inherit = "sale.order"

    @api.multi
    def _workflow_history_count(self):
        for op in self:
            workflow_history = self.env['res.workflow.history'].search([('model', '=', 'sale.order'), ('res_id', '=', op.id)])
            op.workflow_history_count = len(workflow_history)

    @api.multi
    def _get_auditor_is_user(self):
        for op in self:
            op.auditor_is_user = op.auditor == self.env.user

    # 审核专用字段，请勿修改
    workflow_state = fields.Boolean(string=u'审核状态')
    auditor = fields.Many2one('res.users', string=u'当前处理人')
    workflow_id = fields.Integer(string=u'流程ID')
    rule_sequence = fields.Integer(string=u'下一个规则序列')
    handle_reason = fields.Text(u'原因')
    workflow_history_count = fields.Integer(compute='_workflow_history_count', string=u'操作历史')
    # state = fields.Selection(selection_add=[('checking', u'审核中'), ('reject', u'驳回')])
    state = fields.Selection([
        ('draft', u'报价单'),
        ('sent', u'报价单送出'),
        ('checking', u'审核中'),
        ('reject', u'驳回'),
        ('sale', u'销售订单'),
        ('done', u'完成'),
        ('cancel', u'已取消'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    auditor_is_user = fields.Boolean(compute='_get_auditor_is_user', string=u"登录人事处理人")
    validity_date = fields.Date(string='Expiration Date', readonly=True,
                                states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'reject': [('readonly', False)]})
    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True,
                       states={'draft': [('readonly', False)], 'reject': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    date_order = fields.Datetime(string='Order Date', required=True, readonly=True, index=True,
                                 states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'reject': [('readonly', False)]}, copy=False,
                                 default=fields.Datetime.now)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True,
                                 states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'reject': [('readonly', False)]}, required=True,
                                 change_default=True, index=True, track_visibility='always')
    contact_id = fields.Many2one('res.partner', string='联系人', readonly=True,
                                 states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'reject': [('readonly', False)]},
                                 change_default=True, index=True, track_visibility='always')
    partner_invoice_id = fields.Many2one('res.partner', string='Invoice Address', readonly=True, required=True,
                                         states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'reject': [('readonly', False)]},
                                         help="Invoice address for current sales order.")
    partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address', readonly=True, required=True,
                                          states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'reject': [('readonly', False)]},
                                          help="Delivery address for current sales order.")

    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', required=True, readonly=True,
                                   states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'reject': [('readonly', False)]},
                                   help="Pricelist for current sales order.")
    project_id = fields.Many2one('account.analytic.account', 'Analytic Account', readonly=True,
                                 states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'reject': [('readonly', False)]},
                                 help="The analytic account related to a sales order.", copy=False)

    # 提交
    @api.one
    def button_submit(self):
        # 检查是否安装流程模块，如果没有安装，提交后直接设置成完成状态
        if not self.env['ir.model'].search([('model', '=', 'res.workflow')]):
            # self.state = 'done'
            super(workflow_sale, self).action_confirm()
        # 提交单据，检查是否配置流程
        workflow_list = self.env['res.workflow'].search([('res_model', '=', 'sale.order')])
        workflow_flg = False
        workflow_id = 0
        for workflow in workflow_list:
            # 获取流程启用规则，判断当前单据时候存在可用流程
            domain = []
            for rule in workflow.res_workflow_rule:
                model_condition = rule.model_condition  # 判断条件
                a = u"为真"
                b = u"设置"
                c = u"未设置"
                d = u"为假"
                if model_condition == b or model_condition == a:
                    domain.append([rule.model_fields.name, "!=", False])
                elif model_condition == c or model_condition == d:
                    domain.append([rule.model_fields.name, "=", False])
                else:
                    model_condition = self.string_to_operators(model_condition)
                    domain.append([rule.model_fields.name, model_condition, rule.model_fields_input])
            if self.search([('id', '=', self.id)] + domain):
                workflow_flg = True
                # 执行流程
                workflow_dtl = self.env['res.workflow.dtl'].search([('workflow_id', '=', workflow.id), ('sequence', '=', '1')])
                if workflow_dtl:
                    # 如果审核人类型是‘审核人’，直接发消息
                    user = self._get_user(workflow_dtl)
                    # 给处理人发送消息
                    self.message_post(body=_("%s 销售订单 %s 等待 %s 审核!") % (self.user_id.employee_id.name, self.name, user.partner_id.name), subject="RE:单据变更提醒",
                                      message_type="comment",
                                      content_subtype='html', subtype_id=1, partner_ids=list(set([user.partner_id.id])))
                    # 更新字段
                    self.update({'workflow_state': True, 'auditor': user, 'rule_sequence': "2", 'state': 'checking', 'workflow_id': workflow.id})
                    # 创建处理历史和待办
                    self.create_workflow_history(user, {'handle_result': "提交"})
                else:
                    # self.state = 'done'
                    super(workflow_sale, self).action_confirm()  # 确认订单
                break
        if not workflow_flg:
            # self.state = 'done'
            super(workflow_sale, self).action_confirm()  # 确认订单
        return True

    # 撤回
    @api.one
    def button_cancel(self):
        # if self.rule_sequence != 2:
        #     raise ValidationError(_("单据已审核，不能撤回!"))
        # 创建处理历史和待办
        self.cancel_workflow_history({'handle_result': '撤回'})
        super(workflow_sale, self).action_cancel()
        return True

    # 驳回
    @api.one
    def button_reject(self):
        # 将单据退回给创建人、修改状态并发送通知
        self.message_post(body=_("%s 销售订单 %s 被 %s 驳回!") % (self.user_id.employee_id.name, self.name, self.env.user.partner_id.name), subject="RE:单据变更提醒",
                          message_type="comment",
                          content_subtype='html', subtype_id=1,
                          partner_ids=list(set([self.create_uid.partner_id.id])))
        self.update({'auditor': self.create_uid, 'rule_sequence': "1", 'state': 'reject'})
        # 创建处理历史和待办
        self.create_workflow_history(self.create_uid, {'handle_result': '驳回', 'handle_reason': self.handle_reason})
        return True

    @api.one
    def button_ok(self):
        workflow_dtl = self.env['res.workflow.dtl'].search(
            [('workflow_id', '=', self.workflow_id), ('sequence', '=', self.rule_sequence)])
        # 判断是否存在下一个节点，如果不存在。单据完成
        if not workflow_dtl:
            # 跟新待办为历史
            need_workflow = self.env['res.workflow.history'].search(
                [('auditor_id', '=', self.env.uid), ('handle_type', '=', 'need'), ('res_id', '=', self.id),
                 ('model', '=', self._name)])
            if need_workflow:
                need_workflow.write(
                    {'handle_time': datetime.datetime.now(), 'handle_result': '通过',
                     'handle_type': 'history'})
            self.update({'workflow_state': False, 'auditor': None, 'rule_sequence': None, 'workflow_id': None})
            # 审核通过，给申请人发送一个消息
            self.message_post(
                body=_("%s 销售订单 %s 已审核通过!") % (self.user_id.employee_id.name, self.name),
                subject="RE:单据变更提醒",
                message_type="comment",
                content_subtype='html', subtype_id=1, partner_ids=list(set([self.create_uid.partner_id.id])))
            # 执行确认订单
            super(workflow_sale, self).action_confirm()
        # 如果存在，继续执行流程
        if workflow_dtl:
            self._process_continues(workflow_dtl, self.workflow_id, self.rule_sequence)
        return True

    def _process_continues(self, workflow_dtl, workflow_id, rule_sequence):
        # 如果审核人类型是‘审核人’，直接发消息
        user = self._get_user(workflow_dtl)
        # 给处理人发送消息
        self.message_post(body=_("%s 销售订单 %s 等待 %s 审核!") % (self.user_id.employee_id.name, self.name, user.partner_id.name), subject="RE:单据变更提醒",
                          message_type="comment",
                          content_subtype='html', subtype_id=1,
                          partner_ids=list(set([user.partner_id.id])))
        # 更新字段
        self.update({'workflow_state': True, 'auditor': user, 'rule_sequence': rule_sequence+1, 'state': 'checking',
                     'workflow_id': workflow_id})
        # 创建处理历史和待办
        self.create_workflow_history(user, {'handle_result': "通过"})

    @api.multi
    def get_formview_id(self):
        """ Update form view id of action to open the invoice """
        if self.state == "reject":
            return self.env.ref('sale.view_order_form').id
        else:
            return self.env.ref('base_workflow.sale_order_workflow_form').id

    def string_to_operators(self, argument):
        switcher = {
            u'等于': "=",
            u'不等于': "!=",
            u'大于': ">",
            u'小于': "<",
            u'大于等于': ">=",
            u'小于等于': "<=",
            u'包含': "in",
            u'不包含': "not in",
        }
        return switcher.get(argument)

    def create_workflow_history(self, auditor , handle_result):
        # 查看当前登录人是否有待办
        need_workflow = self.env['res.workflow.history'].search([('auditor_id', '=', self.env.uid), ('handle_type', '=', 'need'), ('res_id', '=', self.id), ('model', '=', self._name)])
        if need_workflow:
            submit_person = need_workflow.submit_person.id
            need_workflow.write({'handle_time': datetime.datetime.now(), 'handle_result': handle_result.get('handle_result', False), 'handle_type': 'history', 'handle_reason': handle_result.get('handle_reason', False)})
        else:
            # 插入处理历史
            submit_person = self.env.uid
            values = {
                'model': self._name,
                'res_id': self.id,
                'into_person': self.env.uid,
                'into_time': datetime.datetime.now(),
                'auditor_id': self.env.uid,
                'handle_time': datetime.datetime.now(),
                'handle_result': handle_result.get('handle_result', False),
                'handle_type': 'history',
                'model_name': "销售订单",
                'submit_person': submit_person  # 保存提交人
            }
            self.env['res.workflow.history'].create(values)  # 创建单据提交历史
        aa = handle_result.get('handle_result', False)
        if aa != "驳回":
            values = {
                'model': self._name,
                'res_id': self.id,
                'into_person': self.env.uid,
                'into_time': datetime.datetime.now(),
                'auditor_id': auditor.id,
                'handle_type': 'need',
                'model_name': "销售订单",
                'submit_person': submit_person  # 保存提交人
            }
            self.env['res.workflow.history'].create(values)  # 创建审核人待办

    def cancel_workflow_history(self, handle_result):
        # 删除当前待办，创建撤回历史
        need_workflow = self.env['res.workflow.history'].search([('handle_type', '=', 'need'), ('res_id', '=', self.id),
             ('model', '=', self._name)])
        submit_person = need_workflow.submit_person.id
        if need_workflow:
            # 删除通知消息
            self.delete_message_by_state(need_workflow.auditor_id)
            need_workflow.unlink()
        # 插入处理历史
        values = {
            'model': self._name,
            'res_id': self.id,
            'into_person': self.env.uid,
            'into_time': datetime.datetime.now(),
            'auditor_id': self.env.uid,
            'handle_time': datetime.datetime.now(),
            'handle_result': handle_result.get('handle_result', False),
            'handle_type': 'history',
            'model_name': "销售订单",
            'submit_person': submit_person  # 保存提交人
        }
        self.env['res.workflow.history'].create(values)  # 创建单据提交历史

    def delete_message_by_state(self, user):
        # 退回完成后，删除通知
        partner_id = user.partner_id
        messages = self.env['mail.message'].search(
            [('res_id', '=', self.id), ('model', '=', 'sale.order')]).filtered(
            lambda msg: partner_id in msg.needaction_partner_ids)
        if not len(messages):
            return
        messages.sudo().write({'needaction_partner_ids': [(3, partner_id.id)]})

    def _get_user(self, workflow_dtl):
        if workflow_dtl.person_type == '1':
            user = workflow_dtl.auditor
        elif workflow_dtl.person_type == '2':  # 主管
            login_hr = self.env['hr.employee'].search([('user_id', '=', self.create_uid.id)])
            user = login_hr.parent_id.user_id
            if not user:
                raise ValidationError(_("主管 %s 没有指定用户，请联系人事维护员工信息。") % login_hr.name)
        else:  # 组长
            login_hr = self.env['hr.employee'].search([('user_id', '=', self.create_uid.id)])
            user = login_hr.coach_id.user_id
            if not user:
                raise ValidationError(_("组长 %s 没有指定用户，请联系人事维护员工信息。") % login_hr.name)
        return user
