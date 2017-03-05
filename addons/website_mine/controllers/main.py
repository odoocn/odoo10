# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import http
from odoo.http import request, Controller
import json

logger = logging.getLogger(__name__)

class WebsiteProduct(http.Controller):
    # 产品页
    @http.route('/product', type='http', auth="public", website=True, cache=300)
    def WebsiteProduct(self):
        return request.render('website_mine.product')

# class JsPython(Controller):
#     @http.route(['/run_python/<string:url>', ], type='http', auth="public")
#     def run_python(self, url):
#         third_content = request.env['dvt.third.content'].sudo().search([('url', '=', url)])
#         result = {
#             'html': third_content.html,
#         }
#         return json.dumps(result)