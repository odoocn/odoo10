# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import http
from odoo.http import request, Controller
import json

logger = logging.getLogger(__name__)

class WebsitePortal(http.Controller):
    @http.route('/aboutrsf/<string:string>', type='http', auth="public", website=True, cache=300)
    def aboutrsf(self, string):
        values = {
            'name': u'廖小满',
        }
        url = 'dvt_portal.'+string
        return request.render(url, values)

    # 一级菜单下的内容
    @http.route('/rsf/<string:first>', type='http', auth="public", website=True, cache=300)
    def first(self, first):
        first_content = request.env['dvt.first.content'].sudo().search([('url', '=', first), ('type', '=', 'details')])
        if not first_content:
            return request.render('website.404')
        values = {"first_content": first_content,}
        return request.render('dvt_portal.first', values)

    # 二级菜单下的内容
    @http.route('/rsf/<string:first>/<string:second>', type='http', auth="public", website=True, cache=300)
    def second(self, first, second):
        first_content = request.env['dvt.first.content'].sudo().search([('url', '=', first)])
        second_content = request.env['dvt.second.content'].sudo().search([('belong_to', '=', first_content.id)])
        active_content = request.env['dvt.second.content'].sudo().search([('url', '=', second)])
        if not active_content or active_content.id not in second_content.ids:
            return request.render('website.404')
        values = {
            'first_content': first_content,
            'second_content': second_content,
            'active_content': active_content,
        }
        if active_content.type == 'content':
            third_content = request.env['dvt.third.content'].sudo().search([('belong_to', '=', active_content.id)])
            pages = len(third_content.ids)/8 + 1
            values['third_content'] = third_content[0:8]
            if pages != 1:
                values['pages'] = [1, pages]
        return request.render('dvt_portal.second', values)

    # 联系我们
    @http.route('/rsf/contactus', type='http', auth="public", website=True, cache=300)
    def contactus(self):
        return request.render('dvt_portal.contactus')

class JsPython(Controller):
    @http.route(['/run_python/<string:url>', ], type='http', auth="public")
    def run_python(self, url):
        third_content = request.env['dvt.third.content'].sudo().search([('url', '=', url)])
        result = {
            'html': third_content.html,
        }
        return json.dumps(result)


    @http.route(['/turn_to/<string:second>/<string:page>', ], type='http', auth="public")
    def turn_to(self, second, page):
        active_content = request.env['dvt.second.content'].sudo().search([('url', '=', second)])
        third_content = request.env['dvt.third.content'].sudo().search([('belong_to', '=', active_content.id)])
        p = int(page) - 1
        data = []
        for i in third_content[(0+8*p):(8+8*p)]:
            the_third_content = {'name': i.name, 'url': i.url, 'date': i.date, 'id': i.id}
            data.append(the_third_content)
        return json.dumps({'third_content': data})