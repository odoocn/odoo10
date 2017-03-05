# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo import api, _


class res_workflow(models.Model):
    _inherit = "account.move"

    @api.multi
    def button_workflow_report(self):
        ids = []
        for ld in self:
            ids += [pick for pick in ld.ids]
        aaa=self.env["report"].with_context(active_ids=ids, active_model='account.move')
        return aaa.get_action(self,'base_workflow.workflow_report')
