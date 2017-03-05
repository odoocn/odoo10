# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class AlertDialog(models.Model):
    _name = "tools.alert.dialog"

    name = fields.Char(string=u'提示')

    @api.one
    def finish(self):
        return self.unlink()

    def alert_dialog(self, cr, uid, msg, context=None):
        imd = self.pool['ir.model.data']
        action = imd.xmlid_to_object(cr, uid, 'driserp.act_alert_dialog_new')
        form_view_id = imd.xmlid_to_res_id(cr, uid, 'driserp.view_alert_dialog_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form']],
            'target': action.target,
            'context': {'default_name': msg},
            'res_model': action.res_model,
        }
        return result

    @api.multi
    def new_alert(self, msg):
        alert = self.create({'name': msg})
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('driserp.act_alert_dialog_new')
        form_view_id = imd.xmlid_to_res_id('driserp.view_alert_dialog_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [(form_view_id, 'form')],
            'target': action.target,
            'context': {'default_name': msg},
            'res_model': action.res_model,
            'res_id': alert.id
        }
        return result
