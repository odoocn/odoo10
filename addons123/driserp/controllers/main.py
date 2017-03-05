# -*- coding: utf-8 -*-
import logging
import odoo

from odoo import http
from odoo.http import request
from odoo.exceptions import UserError
import datetime
import urllib
import urllib2
import json
import time
import werkzeug
import base64


class EcpsController(odoo.addons.web.controllers.main.Home):
    def md5(self, pwd):
        import hashlib
        m = hashlib.md5()
        m.update(pwd)
        return m.hexdigest()

    @http.route('/', type='http', auth="none")
    def index(self, state=None, code=None, debug=False, **kwargs):
        if not kwargs.get('sign'):
            return http.local_redirect('/web', query=request.params, keep_hash=True)
        res = request.env['ecps.shop'].sudo().search([('last_sign', '=', kwargs['sign'])])
        if len(res) == 0:
            return http.local_redirect('/web', query=request.params, keep_hash=True)
        res = res[0]
        res.sudo().write({'access_in': datetime.datetime.strptime(kwargs['access_in'], '%Y-%m-%d %H:%M:%S'),
                          'expires_in': datetime.datetime.strptime(kwargs['access_out'], '%Y-%m-%d %H:%M:%S'),
                          'access_token': kwargs['access_token'],
                          'refresh_token': kwargs['refresh_token']})
        return werkzeug.utils.redirect('/')

    @http.route(['/request_auth', '/web/request_auth'], type='http', auth='user')
    def request_auth(self, shop_id, req_url, debug=False, **k):
        shop = request.env['ecps.shop'].browse(int(shop_id))
        # req_url = "http://101.201.75.114:8089/"
        # req_url = "http://" + request.env.cr.dbname + ".drissaas.com/"
        url = "http://www.drissaas.com/new_auth?request_api=" + shop.plate_id.plate_api.encode('utf-8') + "&sign=" + \
              shop.compute_sign()[0].encode('utf-8') + "&req_url=" + req_url
        return werkzeug.utils.redirect(url.encode('utf-8'))

    @http.route(['/get_express_code'], type='http', auth='user', csrf=False)
    def get_express_code(self, order_id, **k):
        order = request.env['sale.order'].browse(order_id)
        web_url = order.express_com.code_api
        options = "{'ShipperCode':'" + order.express_com.code.encode('utf-8') + "'," + \
                  "'IsReturnPrintTemplate':'1'," + \
                  "'OrderCode':'" + order.name.encode('utf-8') + "'," + \
                  "'PayType':'" + order.express_paytype.encode('utf-8') + "'," + \
                  "'ExpType':'1','Receiver':{" + \
                  "'Name':'" + order.delivery_name.encode('utf-8') + "'," + \
                  "'Tel':'" + order.delivery_phone.encode('utf-8') + "'," + \
                  "'ProvinceName':'" + order.location_province.name.encode('utf-8') + "'," + \
                  "'CityName':'" + order.location_city.name.encode('utf-8') + "'," + \
                  "'ExpAreaName':'" + order.location_district.name.encode('utf-8') + "'," + \
                  "'Address':'" + order.location_details.encode('utf-8') + "'},'Sender':{" + \
                  "'Name':'" + order.delivery_name.encode('utf-8') + "'," + \
                  "'Tel':'" + order.delivery_phone.encode('utf-8') + "'," + \
                  "'ProvinceName':'" + order.location_province.name.encode('utf-8') + "'," + \
                  "'CityName':'" + order.location_city.name.encode('utf-8') + "'," + \
                  "'ExpAreaName':'" + order.location_district.name.encode('utf-8') + "'," + \
                  "'Address':'" + order.location_details.encode('utf-8') + "'}" + ",'Commodity':["
        for line in order.order_line:
            options += ("{'GoodsName':'" + line.product_id.name.encode('utf-8') + "'},")
        options = options[:-1]
        options += "]}"
        datas = {}
        datas['RequestData'] = urllib.quote(options)
        datas['RequestType'] = '1007'
        datas['DataType'] = '2'
        datas['EBusinessID'] = order.express_com.EBusinessID.encode('utf-8')
        datas['DataSign'] = urllib.quote(
            base64.b64encode(self.md5(options + order.express_com.appKey.encode('utf-8'))))
        temp = []
        for key in datas.keys():
            temp.append(key + "=" + datas[key])
        data = "&".join(temp)
        req = urllib2.Request(web_url.encode('utf-8'), data, {'Content-type': "application/x-www-form-urlencoded"})
        content = urllib2.urlopen(req, timeout=60).read()
        content = json.loads(content)
        if content['ResultCode'] == u'100':
            result = ""
        else:
            pass

    @http.route(['/get_expresses'], type='http', auth='user', csrf=False)
    def get_expresses(self, wave_id, **k):
        wave = request.env['stock.picking.wave'].browse(int(wave_id))
        result = {}
        for picking in wave.picking_ids:
            datas = {}
            web_url = picking.sale_id.express_com.express_api
            options = "{'ShipperCode':'" + picking.sale_id.express_com.code.encode('utf-8') + "'," + \
                      "'IsReturnPrintTemplate':'1'," + \
                      "'OrderCode':'" + picking.sale_id.name.encode('utf-8') + "'," + \
                      "'PayType':'" + picking.sale_id.express_paytype.encode('utf-8') + "'," + \
                      "'ExpType':'1','Receiver':{" + \
                      "'Name':'" + picking.sale_id.delivery_name.encode('utf-8') + "'," + \
                      "'Tel':'" + picking.sale_id.delivery_phone.encode('utf-8') + "'," + \
                      "'ProvinceName':'" + picking.sale_id.location_province.name.encode('utf-8') + "'," + \
                      "'CityName':'" + picking.sale_id.location_city.name.encode('utf-8') + "'," + \
                      "'ExpAreaName':'" + picking.sale_id.location_district.name.encode('utf-8') + "'," + \
                      "'Address':'" + picking.sale_id.location_details.encode('utf-8') + "'},'Sender':{" + \
                      "'Name':'" + picking.sale_id.source_shop.delivery_name.encode('utf-8') + "'," + \
                      "'Tel':'" + picking.sale_id.source_shop.delivery_phone.encode('utf-8') + "'," + \
                      "'ProvinceName':'" + picking.sale_id.source_shop.location_province.name.encode('utf-8') + "'," + \
                      "'CityName':'" + picking.sale_id.source_shop.location_city.name.encode('utf-8') + "'," + \
                      "'ExpAreaName':'" + picking.sale_id.source_shop.location_district.name.encode('utf-8') + "'," + \
                      "'Address':'" + picking.sale_id.source_shop.location_details.encode(
                'utf-8') + "'}" + ",'Commodity':["
            for move in picking.move_lines:
                options += ("{'GoodsName':'" + move.product_id.name.encode('utf-8') + "'},")
            options = options[:-1]
            options += "]}"
            datas['RequestData'] = urllib.quote(options)
            datas['RequestType'] = '1007'
            datas['DataType'] = '2'
            datas['EBusinessID'] = picking.sale_id.express_com.EBusinessID.encode('utf-8')
            datas['DataSign'] = base64.b64encode(self.md5(options + picking.sale_id.express_com.appKey.encode('utf-8')))
            temp = []
            for key in datas.keys():
                temp.append(key + "=" + datas[key])
            data = "&".join(temp)
            req = urllib2.Request(web_url.encode('utf-8'), data, {'Content-type': "application/x-www-form-urlencoded"})
            content = urllib2.urlopen(req, timeout=60).read()
            content = json.loads(content)
            if content['ResultCode'] == u'100':
                result[picking.id] = content['PrintTemplate'].replace("<head>", '<head><meta charset="UTF-8">')
                result[picking.id] = result[picking.id].encode('utf-8')
            else:
                pass
        return json.dumps(result)

    @http.route(['/get_box'], type='http', auth='user', csrf=False)
    def get_box(self, wave_id, **k):
        boxes = request.env['ecps.box'].search([('wave_id', '=', int(wave_id)), ('printed', '=', False)])
        response = {'result': []}
        for box in boxes:
            response['result'].append(box.get_html())
        return json.dumps(response)

    @http.route('/web/export/excel/', type='http', auth='user', csrf=False)
    def from_data(self, **post):
        attributes_obj = request.registry['stock.picking.wave']
        data = attributes_obj.print_pickings_excel(request.cr, 1, post, request.context)
        if data == False:
            print u'没有获取到wave_id' 
            return False
        else:
            return request.make_response(data, headers=[
                ('Content-Disposition', self.content_disposition(self.filename(u'捡货波次-交货单'))),
                ('Content-Type', 'application/vnd.ms-excel')])

    @http.route('/web/export/excel2/', type='http', auth='user', csrf=False)
    def from_data2(self, **post):
        attributes_obj = request.registry['stock.picking.wave']
        data = attributes_obj.print_product_excel(request.cr, 1, post, request.context)
        if data == False:
            print u'没有获取到wave_id' 
            return False
        else:
            return request.make_response(data, headers=[
                ('Content-Disposition', self.content_disposition(self.filename(u'捡货波次-产品'))),
                ('Content-Type', 'application/vnd.ms-excel')])

    @http.route('/web/export/excel3/', type='http', auth='user', csrf=False)
    def from_data3(self, **post):
        attributes_obj = request.registry['stock.picking.wave']
        data = attributes_obj.print_product_mark_excel(request.cr, 1, post, request.context)
        if data == False:
            print u'没有获取到wave_id' 
            return False
        else:
            return request.make_response(data, headers=[
                ('Content-Disposition', self.content_disposition(self.filename(u'捡货波次-大头笔'))),
                ('Content-Type', 'application/vnd.ms-excel')])

    # 交货单打印发货单
    @http.route('/web/export/picking', type='http', auth='user', csrf=False)
    def print_delivery_picking(self, picking_id, **post):
        attributes_obj = request.env['stock.picking'].browse(int(picking_id))
        data = attributes_obj.print_delivery_picking()
        if data == False:
            print u'没有获取到wave_id'
            return False
        else:
            return request.make_response(data, headers=[
                ('Content-Disposition', self.content_disposition(self.filename(u'发货单-%s' % attributes_obj.sale_id.source_code))),
                ('Content-Type', 'application/vnd.ms-excel')])

    # 交货单打印备货单
    @http.route('/web/export/picking_ready', type='http', auth='user', csrf=False)
    def print_ready_picking(self, picking_id, **post):
        attributes_obj = request.env['stock.picking'].browse(int(picking_id))
        data = attributes_obj.print_ready_picking()
        if data == False:
            print u'没有获取到wave_id'
            return False
        else:
            return request.make_response(data, headers=[
                ('Content-Disposition', self.content_disposition(self.filename(u'备货单-%s' % attributes_obj.sale_id.source_code))),
                ('Content-Type', 'application/vnd.ms-excel')])

    def content_disposition(self, filename):
        return request.registry['ir.http'].content_disposition(filename)

    def filename(self, base):
        return base + '.xls'
