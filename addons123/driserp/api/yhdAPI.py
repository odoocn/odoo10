# -*- coding: utf-8 -*-

import urllib2
import json
import datetime
import logging


class YHDAPI(object):
    """For YHD Vendors API"""
    WEB_URL = "http://openapi.yhd.com/app/api/rest/router?"
    METHOD_LIST = {'sychronize_orders': 'yhd.supplier.order.po.get',
                   'get_order_details': 'yhd.supplier.order.detail.get',
                   'orders_get': 'yhd.supplier.orders.get',
                   'sychronize_price': 'yhd.products.price.get',
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
            if key in ('timestamp', 'startDate', 'endDate'):
                sign += key + options[key]
            else:
                sign += key + options[key].replace(' ', '')
        sign += self.secret
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
            if option[0] in ('timestamp', 'startDate', 'endDate'):
                opt.append('='.join((option[0], str(option[1]))))
            else:
                opt.append('='.join((option[0], str(option[1]).replace(' ', ''))))
        data = '&'.join(opt)
        req = urllib2.Request(YHDAPI.WEB_URL, data)
        content = urllib2.urlopen(req).read()
        content = json.loads(content)
        return content

    def get_timestamp(self):
        now = datetime.datetime.utcnow()
        eight_hours = datetime.timedelta(hours=8)
        return (now + eight_hours).strftime('%Y-%m-%d %H:%M:%S')

    def sychronize_orders(self, order_ids=False, last_time=False, shop_type=False):
        pageRows = 100
        poStatus = [False]
        res = {'code': 0, 'result': [], 'errorList': []}
        if order_ids:
            order_ids = order_ids[0][3:-1]
        else:
            poStatus = ['0', '1', '2', '3']
        for status in poStatus:
            curPage = 1
            recount = 0
            totalCount = 99999
            while recount < totalCount:
                options = {'appKey': self.appKey.encode('utf-8'),
                           'method': YHDAPI.METHOD_LIST['sychronize_orders'],
                           'ver': '1.0',
                           'sessionKey': self.access_token,
                           'format': 'json',
                           'timestamp': self.get_timestamp(),
                           'curPage': curPage,
                           'pageRows': pageRows,
                           'poType': '0'
                           }
                if last_time:
                    options['startDate'] = last_time
                    options['endDate'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if order_ids:
                    options['id'] = order_ids
                if status:
                    options['poStatus'] = status
                options['sign'] = self.sign(options=options)
                content = self.get_response(options)
                response = content['response']
                totalCount = response.get('totalCount', 0)
                if not response.get('errInfoList'):
                    curPage += 1
                    recount += pageRows
                    totalCount = response.get('totalCount', 0)
                    if totalCount == 0 and order_ids:
                        return {'code': -1, 'result': u"未查到订单 %s 订单信息" % order_ids}
                    if totalCount > 0:
                        for po in content['response']['polist']['po']:
                            if po['poStatus'] in (5, 8):
                                order_step = 2
                            elif po['poStatus'] == 9:
                                order_step = -1
                            elif po['poStatus'] in (2, 3, 4):
                                order_step = 1
                            else:
                                order_step = 0
                            order_state_dict = {0: "待批准",
                                                1: "批准",
                                                2: "待收货",
                                                3: "部分收货",
                                                4: "拒绝收货",
                                                5: "完成",
                                                6: "终止",
                                                7: "等待取消",
                                                8: "退货完成",
                                                9: "作废"}
                            res['result'].append({'source_code': (po['poCode']),
                                                  'order_state': order_state_dict[po['poStatus']],
                                                  'order_start_time': po['poOrderDate'],
                                                  'order_end_time': po.get('actualDeliveryDate', False),
                                                  'delete_mark': False,
                                                  # 'location_details': po['goodReceiverProvince'] + po['goodReceiverCity'] +
                                                  #  po['goodReceiverCounty'] + po['goodReceiverAddress'],
                                                  'location_details': '',
                                                  'location_mark': '',
                                                  'location_province': False,
                                                  'location_city': False,
                                                  'location_district': False,
                                                  'order_step': order_step,
                                                  'deliverCenterId': False,
                                                  'confirm_need': False,
                                                  'return_state': False,
                                                  'deliverCenterName': po['wareHouseName'],
                                                  'warehouseName': po['wareHouseName'],
                                                  'delivery_name': '',
                                                  'delivery_phone': '',
                                                  'details': [],
                                                  'pur_erp': False
                                                  })
                            for poitem in po['poItemList']['poItem']:
                                res['result'][-1]['details'].append({
                                    'price': float(poitem['poItemInPrice']),
                                    'sku_id': poitem['pmCode'],
                                    'num': float(poitem.get('expectedAvailabilityNum', 0)),
                                    'actualNum': float(poitem.get('actualDeliveryNum', 0)),
                                    'originalNum': poitem.get('poItemNum', 0),
                                    'remark': '',
                                })
                            res['last_time'] = po['poOrderDate']
                elif curPage != 1:
                    curPage += 1
                    recount += pageRows
                    res['errorList'].append(content['response']['errInfoList']['errDetailInfo'][0]['errorDes'])
                    res['code'] = 1
                else:
                    res = {'code': -1, 'result': content['response']['errInfoList']['errDetailInfo'][0]['errorDes']}
        return res

    def sychronize_price(self, sku=None):
        res = {'code': 0}
        skulist = []
        skulist.append(sku)
        options = {'appKey': self.appKey.encode('utf-8'),
                   'sessionKey': self.access_token,
                   'method': YHDAPI.METHOD_LIST['sychronize_price'],
                   'ver': '1.0',
                   'format': 'json',
                   'timestamp': self.get_timestamp(),
                   'productIdList': skulist,
                   }
        options['sign'] = self.sign(options=options)
        content = self.get_response(options)
        response = content['response']
        if response.get('pmPriceList'):
            po = response['pmPriceList']['pmPrice'][0]
            res['result'] = {
                'purchase_price': po['inPrice'],
                'member_price': po['nonMemberPrice'],
                'market_price': po['productListPrice']
            }
        else:
            res = {'code': -1, 'result': content['response']['errInfoList']['errDetailInfo'][0]['errorDes']}
        return res

    def sychronize_info(self, code, sku):
        totalCount = 99999
        recount = 0
        curPage = 1
        pageRows = 100
        res = {'code': 0, 'result': {}}
        while totalCount >= pageRows:
            options = {
                'appKey': self.appKey,
                'sessionKey': self.access_token,
                'format': 'json',
                'ver': '1.0',
                'method': YHDAPI.METHOD_LIST['sychronize_info'],
                'timestamp': self.get_timestamp(),
                'productIdList': code,
                'curPage': curPage,
                'pageRows': pageRows,
            }
            options['sign'] = self.sign(options=options)
            content = self.get_response(options)
            response = content['response']
            totalCount = response['totalCount']
            if response.get('productList'):
                recount += pageRows
                for po in response['productList']['product']:
                    res['result'] = {
                        'name': po['productCname'],
                        'brand': False,
                        'barcode': po.get('ean13', ''),
                        'category': False,
                        'url': '',
                        'purchase_price': False,
                        'member_price': False,
                        'market_price': False
                    }
            else:
                res = {'code': -1, 'result': response['errInfoList']['errDetailInfo'][0]['errorDes']}
            curPage += 1
        return res

    def sychronize_categories(self):
        res = {'code': 0, 'result': []}
        options = {
            'appKey': self.appKey,
            'sessionKey': self.access_token,
            'format': 'json',
            'ver': '1.0',
            'method': YHDAPI.METHOD_LIST['sychronize_categories'],
            'timestamp': self.get_timestamp(),
        }
        options['sign'] = self.sign(options=options)
        content = self.get_response(options)
        response = content['response']
        if response.get('categoryList'):
            for po in response['categoryList']['category']:
                res['result'].append({'id': '',
                                      'name': po['categoryName'],
                                      })
        else:
            res = {'code': -1, 'result': response['errInfoList']['errDetailInfo'][0]['errorDes']}
        return res

    def sychronize_brand(self):
        res = {'code': 0, 'result': []}
        options = {
            'appKey': self.appKey,
            'sessionKey': self.access_token,
            'format': 'json',
            'ver': '1.0',
            'method': YHDAPI.METHOD_LIST['sychronize_brand'],
            'timestamp': self.get_timestamp(),
        }
        options['sign'] = self.sign(options=options)
        content = self.get_response(options)
        response = content['response']
        if response.get('brandList'):
            for po in response['brandList']['brand']:
                res['result'].append({
                    'id': '',
                    'name': po['brandName']
                })
        else:
            res = {'code': -1, 'result': response['errInfoList']['errDetailInfo'][0]['errorDes']}
        return res

    def sychronize_items(self, curPage=1, pageRows=100):
        totalCount = 1000
        recount = 0
        res = {'code': 0, 'result': []}
        while totalCount >= pageRows:
            options = {
                'appKey': self.appKey,
                'sessionKey': self.access_token,
                'format': 'json',
                'ver': '1.0',
                'method': YHDAPI.METHOD_LIST['sychronize_items'],
                'timestamp': self.get_timestamp(),
                'curPage': curPage,
                'pageRows': pageRows,
            }
            options['sign'] = self.sign(options=options)
            content = self.get_response(options)
            response = content['response']
            totalCount = response.get('totalCount', totalCount)
            if response.get('productList'):
                curPage += 1
                recount += pageRows
                for product in response['productList']['product']:
                    res['result'].append({
                        'sku': str(product['productCode']),
                        'ware_id': str(product['productId']),
                        'active_status': 'on',
                        'name': product['productCname'],
                        'brand': '',
                        'barcode': product.get('ean13', False),
                        'category': '',
                        'url': '',
                        'purchase_price': False,
                        'member_price': False,
                        'market_price': False,
                    })
            elif recount > 0:
                break
            else:
                res = {'code': -1, 'result': response['errInfoList']['errDetailInfo'][0]['errorDes']}
        return res

    def sychronize_return(self, order_ids=False, last_time=False):
        pageRows = 100
        poStatus = [False]
        res = {'code': 0, 'result': [], 'errorList': []}
        if order_ids:
            order_ids = ','.join(order_ids)
        else:
            poStatus = ['0', '1', '2', '3']
        for status in poStatus:
            curPage = 1
            recount = 0
            totalCount = 99999
            while recount < totalCount:
                options = {'appKey': self.appKey.encode('utf-8'),
                           'method': YHDAPI.METHOD_LIST['sychronize_orders'],
                           'ver': '1.0',
                           'sessionKey': self.access_token,
                           'format': 'json',
                           'timestamp': self.get_timestamp(),
                           'curPage': curPage,
                           'pageRows': pageRows,
                           'poType': '1'
                           }
                if last_time:
                    options['startDate'] = last_time
                    options['endDate'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if order_ids:
                    options['id'] = order_ids
                if status:
                    options['poStatus'] = status
                options['sign'] = self.sign(options=options)
                content = self.get_response(options)
                response = content['response']
                totalCount = response.get('totalCount', 0)
                if not response.get('errInfoList'):
                    curPage += 1
                    recount += pageRows
                    totalCount = response.get('totalCount', 0)
                    if totalCount == 0 and order_ids:
                        return {'code': -1, 'result': u"未查到订单 %s 订单信息" % order_ids}
                    if totalCount > 0:
                        for po in content['response']['polist']['po']:
                            order_state_dict = {0: "待批准",
                                                1: "批准",
                                                2: "待收货",
                                                3: "部分收货",
                                                4: "拒绝收货",
                                                5: "完成",
                                                6: "终止",
                                                7: "等待取消",
                                                8: "退货完成",
                                                9: "作废"}
                            res['result'].append({'name': (po['poCode']),
                                                  'provider_code': po['supplierId'],
                                                  'stock_name': po['wareHouseName'],
                                                  'from_place': po['wareHouseName'],
                                                  'from_address': "",
                                                  'from_phone': "",
                                                  'from_name': "",
                                                  'provider_name': '',
                                                  'to_place': '',
                                                  'out_time': po['poOrderDate'],
                                                  'details': [],
                                                  'order_state': order_state_dict[po['poStatus']]
                                                  })
                            for poitem in po['poItemList']['poItem']:
                                res['result'][-1]['details'].append({
                                    'item_id': poitem['pmCode'],
                                    'return_num': -float(poitem.get('expectedAvailabilityNum', 0)),
                                    'return_price': float(poitem.get('productListPrice', 0)),
                                    'return_actual': -float(poitem.get('expectedAvailabilityNum', 0)),
                                })
                            res['last_time'] = po['poOrderDate']
                elif curPage != 1:
                    curPage += 1
                    recount += pageRows
                    res['errorList'].append(content['response']['errInfoList']['errDetailInfo'][0]['errorDes'])
                    res['code'] = 1
                else:
                    res = {'code': -1, 'result': content['response']['errInfoList']['errDetailInfo'][0]['errorDes']}
        return res

    def sychronize_shop(self):
        return {'code': 0, 'result': {'code': False,
                                      'name': False,
                                      'shop_type': 'vendor'}}
