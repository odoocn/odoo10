# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime


class ErrorInfo(models.Model):
    _name = "error.info"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    _order = "date desc"
    _rec_name = "date"

    date = fields.Datetime(string=u'发生时间')
    done_date = fields.Datetime(string=u'处理时间')
    description = fields.Text(string=u'描述')
    done = fields.Boolean(string=u'已处理', default=False)
    user = fields.Many2one('res.users', string=u'错误发生人')
    auto_error = fields.Selection([('auto', u'自动同步时出错'), ('man', u'人工操作时出错')],
                                  string=u'出错操作来源', default='auto')
    checker = fields.Many2one('res.users', string=u'错误处理人')
    remark = fields.Text(string=u'备注')

    @api.one
    def action_done(self):
        self.write({'done': True,
                    'done_date': datetime.utcnow(),
                    'checker': self.env.context['uid']})

    @api.multi
    def error_info_close(self):
        for e in self:
            e.write({'done': True,
                     'done_date': datetime.utcnow(),
                     'checker': self.env.context['uid']})

    @api.multi
    def error_commit(self, des):
        if self.env.context.get('uid'):
            self.create({'date': datetime.utcnow(),
                         'auto_error': 'man',
                         'user': self.env.context['uid'],
                         'description': des})
        else:
            self.create({'date': datetime.utcnow(),
                         'auto_error': 'auto',
                         'description': des})

    @api.model
    def _needaction_domain_get(self):
        return [('done', '=', False)]
