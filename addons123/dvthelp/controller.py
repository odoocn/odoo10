# -*- coding: utf-8 -*-
from odoo.http import Controller
import re, json
from odoo import http
from odoo.http import request
import logging,time,datetime
import openerp
_logger = logging.getLogger(__name__)


class HELPTITLE(http.Controller):
    @http.route('/get', type='http', auth="public")
    def help(self, **kwargs):
        result = []
        for app in request.env['help.first'].search([]):
            context=[]
            for product in app.name_id:
                context.append({'secname':product.name})
            result.append({'name': app.name,
                           'type': app.type,'title':context})
        return request.render('dvthelp.help_download', {'result': result})

    @http.route('/context', type='http', auth="public")
    def secondtitle(self, **kwargs):
        data=kwargs
        name=data.get('name')
        result = []
        cont=[]
        if name:
            products=request.env['help.first'].search([('name','=',name)])
        else:
            products=request.env['help.first'].search([])
        for app in products:
            context=[]
            for product in app.name_id:
                context.append({'secname':product.name})
            result.append({'name': app.name,
                           'type': app.type,'title':context})
        for app in request.env['help.first'].search([]):
            cont.append({'name': app.name,
                           'type': app.type,})
        return request.render('dvthelp.help_first', {'result': result,'cont':cont})

    @http.route('/second', type='http', auth="public")
    def secondcontent(self, **kwargs):
        data=kwargs
        name=data.get('name')
        result = []
        cont=[]
        if name:
            products=request.env['help.second'].search([('name','=',name)])
        else:
            products=request.env['help.second'].search([])
        for app in products:
            result.append({'context':app.context,'name':name})
        for app in request.env['help.first'].search([]):
            context=[]
            for product in app.name_id:
                context.append({'secname':product.name})
            cont.append({'name': app.name,
                           'type': app.type,'title':context})
        return http.request.render('dvthelp.help_second', {'result': result,'cont':cont})
