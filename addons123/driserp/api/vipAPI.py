# -*- coding: utf-8 -*-

import urllib2
import json
import datetime
import logging


class VIPAPI(object):
    """For Vip Vendors API"""
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
