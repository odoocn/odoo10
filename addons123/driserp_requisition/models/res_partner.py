# -*- coding: utf-8 -*-
# Part of Dris. See LICENSE file for full copyright and licensing details.
import logging
from datetime import datetime, timedelta
from odoo import SUPERUSER_ID
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import json

_logger = logging.getLogger(__name__)


class EResPartner(models.Model):
    _inherit = "res.partner"

    has_invoice_child = fields.Boolean(compute='compute_invoice_bool', store=True)

    @api.depends('child_ids')
    def compute_invoice_bool(self):
        for r in self:
            flag = False
            for child in r.child_ids:
                if child.type == 'invoice':
                    flag = True
            r.has_invoice_child = flag
