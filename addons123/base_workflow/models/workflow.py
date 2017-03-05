# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo import api, _


class res_workflow(models.Model):
    _name = "res.workflow"
    _rec_name = "workflow_name"

    workflow_name = fields.Char(u'流程名称')
    workflow_code = fields.Char(u'流程编码')
    res_model = fields.Selection([('purchase.order', '采购订单'), ('sale.order', '销售订单'), ('requisition.pay', '付款申请'), ('requisition.invoice', '开票申请'), ('hr.expense.sheet', '费用报销')], u'模型名称')
    res_workflow_dtl = fields.One2many('res.workflow.dtl', 'workflow_id', u'流程顺序列表')
    res_workflow_rule = fields.One2many('res.workflow.rule', 'workflow_id', u'流程规则列表')

    @api.model
    def create(self, values):
        index = 1
        for dtl in values.get("res_workflow_dtl"):
            dtl[2]['sequence'] = int(index)
            index += 1
        return super(res_workflow, self).create(values)

    @api.multi
    def write(self, values):
        result = super(res_workflow, self).write(values)
        index = 1
        for dtl in self.res_workflow_dtl:
            dtl.update({"sequence": index})
            index += 1
        return result


class res_workflow_rule(models.Model):
    _name = "res.workflow.rule"

    workflow_id = fields.Many2one('res.workflow', u'流程名称')
    model_fields = fields.Many2one("ir.model.fields", string=u"字段", required=True)
    model_fields_ttype = fields.Char(u"字段类型")
    model_fields_input = fields.Char(u'约束条件')
    model_condition = fields.Char(u'条件')
    input_condition = fields.Char(u'文本条件')

    @api.multi
    def change_model_fields(self, model_fields):
        model_field_info = self.env["ir.model.fields"].browse(model_fields)
        if model_field_info:
            if model_field_info.ttype == "selection":
                select_fields = self.env[model_field_info.model].fields_get(allfields=[model_field_info.name])
                options = ""
                for select in select_fields[model_field_info.name]['selection']:
                    options += "<option value='"+select[0]+"'>"+select[1]+"</option>"
                return {'warning': {
                    'callback': 'this.callback_function("' + model_field_info.ttype + '","'+options+'")',
                }}
            else:
                return {'warning': {
                    'callback': 'this.callback_function("' + model_field_info.ttype + '")',
                }}
        else:
            return {'warning': {
                'callback': 'this.callback_function()',
            }}


class res_workflow_dtl(models.Model):
    _name = "res.workflow.dtl"
    _order = "id"

    workflow_id = fields.Many2one('res.workflow', u'流程名称')
    name = fields.Char(u'节点名称')
    sequence = fields.Integer(u'序列')
    person_type = fields.Selection([('1', '审核人'), ('2', '部门主管'), ('3', '组长')], u'审核人类型')
    auditor = fields.Many2one('res.users', u'审核人')

    @api.model
    def create(self, values):
        return super(res_workflow_dtl, self).create(values)
