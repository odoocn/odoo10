# -*- coding: utf-8 -*-

import urllib2
import json
import datetime
import logging


class TBAPI(object):
    """For TaoBao Vendors API"""
    WEB_URL = 'http://gw.api.taobao.com/router/rest	'
    METHOD_LIST = {'sychronize_orders': 'taobao.trades.sold.get',
                   'get_order_details': 'yhd.supplier.order.detail.get',
                   'orders_get': 'yhd.supplier.orders.get',
                   'sychronize_price': 'yhd.products.price.get ',
                   'sychronize_info': 'yhd.supplier.products.get',
                   'sychronize_categories': 'yhd.supplier.categories.get',
                   'sychronize_brand': 'yhd.supplier.brands.get',
                   'sychronize_items': 'yhd.supplier.products.get',
                   'sychronize_return': 'yhd.refund.detail.get',
                   'get_return_detail': 'yhd.refund.detail.get',
                   'yhd_refund_get': 'yhd.refund.get',
                   }
    HEADERS = {'Content-type': "application/x-www-form-urlencoded"}

    def __init__(self, secret, appkey, access_token):
        self.secret = secret
        self.appKey = appkey
        self.access_token = access_token

    def sign(self, options):
        keys = sorted(options.keys())
        sign = self.secret
        for key in keys:
            if not isinstance(options[key], str):
                options[key] = str(options[key])
            if key == 'timestamp':
                sign += key + options[key]
            else:
                sign += key + options[key].replace(' ', '')
        sign += self.secret
        print sign
        return self.md5(sign)

    def check(self):
        return True

    def md5(self, pwd):
        import hashlib
        m = hashlib.md5()
        m.update(pwd)
        return m.hexdigest()

    def get_response(self, options):
        opt = []
        for option in options.items():
            if option[0] == 'timestamp':
                opt.append('='.join((option[0], str(option[1]))))
            else:
                opt.append('='.join((option[0], str(option[1]).replace(' ', ''))))
        data = '&'.join(opt)
        req = urllib2.Request(TBAPI.WEB_URL, data)
        content = urllib2.urlopen(req).read()
        content = json.loads(content)
        return content

    def get_timestamp(self):
        now = datetime.datetime.utcnow()
        eight_hours = datetime.timedelta(hours=8)
        return (now + eight_hours).strftime('%Y-%m-%d %H:%M:%S')

    def sychronize_orders(self, order_ids=False, shop_type=False, last_time=False):
        totalPage = 99999
        pageIndex = 1
        res = {'code': 0, 'result': []}
        while pageIndex <= totalPage:
            options = {
                'fields': 'tid,type,status,payment,orders,rx_audit_status',
                'method': TBAPI.METHOD_LIST['sychronize_orders'],
                'app_key': self.appKey,
                'session': self.access_token,
                'timestamp': self.get_timestamp(),
                'format': 'json',
                'v': '2.0',
                'sign_method': 'md5',
                '360buy_param_json': {'page_num': str(curPage),
                                      'page_size': str(pageRows),
                                      }
            }
            options['sign'] = self.sign(options=options)
            content = self.get_response(options)
            if content.get('alibaba_tianji_supplier_order_query_response'):
                res['result'].append({
                    ''
                })
