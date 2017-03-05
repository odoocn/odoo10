# -*- coding: utf-8 -*-
import urllib2
import json
import datetime
import logging
import base64


class SuningAPI(object):
    """For SUNING Vendors API"""

    WEB_URL = "http://open.suning.com/api/http/sopRequest?"
    METHOD_LIST = {'sychronize_orders': 'suning.purchaseorder.query',
                   'get_order_details': 'yhd.supplier.order.detail.get',
                   'sychronize_price': 'yhd.products.price.get',
                   'sychronize_info': 'yhd.supplier.products.get',
                   'sychronize_categories': 'suning.custom.category.query',
                   'sychronize_brand': 'suning.custom.newbrand.query',
                   'sychronize_items': 'suning.selfmarket.item.query',
                   'sychronize_return': 'yhd.refund.detail.get',
                   'get_return_detail': 'yhd.refund.detail.get',
                   'yhd_refund_get': 'yhd.refund.get',
                   }
    HEADERS = {'Content-type': "application/x-www-form-urlencoded"}

    def __init__(self, secret, appkey, access_token):
        self.secret = secret
        self.appKey = appkey
        self.access_token = access_token

    def sign(self, options, data):
        strdata = str(data)
        sign = self.secret + options['appMethod'] + options['appRequestTime'] + options['appKey'] + \
               options['versionNo'] + base64.b64decode(strdata)
        return self.md5(sign)

    def check(self):
        return True

    def md5(self, pwd):
        import hashlib
        m = hashlib.md5()
        m.update(pwd)
        return m.hexdigest()

    def get_response(self, options, data):
        req = urllib2.Request(SuningAPI.WEB_URL, data=str(data), headers=options)
        content = urllib2.urlopen(req).read()
        content = json.loads(content)
        return content['sn_responseContent']

    def get_timestamp(self):
        now = datetime.datetime.utcnow()
        eight_hours = datetime.timedelta(hours=8)
        return (now + eight_hours).strftime('%Y-%m-%d %H:%M:%S')

    def sychronize_categories(self):
        pageno = 1
        totalpage = 999999
        res = {'result': [], 'code': 0}
        options = {'appKey': self.appKey.encode('utf-8'),
                   'access_token': self.access_token,
                   'appMethod': SuningAPI.METHOD_LIST['sychronize_categories'],
                   'versionNo': 'v1.2',
                   'format': 'json',
                   'appRequestTime': self.get_timestamp(),
                   'Content-type': 'application/json;charset=UTF-8',
                   "Cache-Control": "no-cache",
                   "Connection": "Keep-Alive"}
        while pageno <= totalpage:
            data = {
                "sn_request": {
                    "sn_body": {
                        "category": {
                            "pageNo": str(pageno),
                            "pageSize": "50",
                        }
                    }
                }
            }
            options['signInfo'] = self.sign(options=options, data=data)
            content = self.get_response(options, data)
            if content.get('sn_error'):
                return {'result': content['sn_error']['error_msg'], 'code': -1}
            else:
                totalpage = int(content['sn_head']['pageTotal'])
                for cate in content['sn_body']['category']:
                    res['result'].append({'id': cate['categoryCode'], 'name': cate['categoryName']})
            pageno += 1
        return res

    def sychronize_brand(self):
        cates = self.sychronize_categories()
        res = {'result': [], 'code': 0}
        if cates['code'] < 0:
            return cates
        cates = cates['result']
        options = {'appKey': self.appKey.encode('utf-8'),
                   'access_token': self.access_token,
                   'appMethod': SuningAPI.METHOD_LIST['sychronize_brand'],
                   'versionNo': 'v1.2',
                   'format': 'json',
                   'appRequestTime': self.get_timestamp(),
                   'Content-type': 'application/json;charset=UTF-8',
                   "Cache-Control": "no-cache",
                   "Connection": "Keep-Alive"}
        for cate in cates:
            pageNo = 1
            totalPage = 999999
            while pageNo <= totalPage:
                data = {
                    "sn_request": {
                        "sn_body": {
                            "queryNewbrand": {
                                "pageNo": str(pageNo),
                                "pageSize": "50",
                                "categoryCode": cate['id']
                            }
                        }
                    }
                }
                options['signInfo'] = self.sign(options=options, data=data)
                content = self.get_response(options, data)
                if content.get('sn_error'):
                    return {'result': content['sn_error']['error_msg'], 'code': -1}
                else:
                    totalPage = int(content['sn_head']['pageTotal'])
                    for brand in content['sn_body']['queryNewbrand']:
                        res['result'].append({'id': brand['brandCode'], 'name': brand['brandName']})
                pageNo += 1
        return res

    def sychronize_items(self):
        pageno = 1
        totalpage = 999999
        res = {'result': [], 'code': 0}
        options = {'appKey': self.appKey.encode('utf-8'),
                   'access_token': self.access_token,
                   'appMethod': SuningAPI.METHOD_LIST['sychronize_items'],
                   'versionNo': 'v1.2',
                   'format': 'json',
                   'appRequestTime': self.get_timestamp(),
                   'Content-type': 'application/json;charset=UTF-8',
                   "Cache-Control": "no-cache",
                   "Connection": "Keep-Alive"}
        while pageno <= totalpage:
            data = {
                "sn_request": {
                    "sn_body": {
                        "queryItem": {
                            "pageNo": str(pageno),
                            "pageSize": "50",
                        }
                    }
                }
            }
            options['signInfo'] = self.sign(options=options, data=data)
            content = self.get_response(options, data)
            if content.get('sn_error'):
                return {'result': content['sn_error']['error_msg'], 'code': -1}
            else:
                totalpage = int(content['sn_head']['pageTotal'])
                for product in content['sn_body']['queryItem']:
                    active_status = 'on' if product['contentStatus'] == "15" else 'off'
                    res['result'].append({'ware_id': product['itemCode'],
                                          'sku': product['productCode'],
                                          'active_status': active_status,
                                          'name': product['cmTitle'],
                                          'brand': product['brandCode'],
                                          'barcode': "",
                                          'category': product['categoryName'],
                                          'url': "http://product.suning.com/" + product['productCode'] + ".html",
                                          'purchase_price': "",
                                          'member_price': "",
                                          'market_price': ""})
            pageno += 1
        return res

    def get_plate(self):
        typecodes = ["1", "2"]
        res = {'result': [], 'code': 0, 'map': []}
        options = {'appKey': self.appKey.encode('utf-8'),
                   'access_token': self.access_token,
                   'appMethod': "suning.plantinfo.query",
                   'versionNo': 'v1.2',
                   'format': 'json',
                   'appRequestTime': self.get_timestamp(),
                   'Content-type': 'application/json;charset=UTF-8',
                   "Cache-Control": "no-cache",
                   "Connection": "Keep-Alive"}
        for type_code in typecodes:
            pageno = 1
            totalpage = 999999
            while pageno <= totalpage:
                data = {
                    "sn_request": {
                        "sn_body": {
                            "queryPlantInfo": {
                                "plantTypeCode": type_code,
                                "pageNo": str(pageno),
                                "pageSize": "50",
                            }
                        }
                    }
                }
                options['signInfo'] = self.sign(options=options, data=data)
                content = self.get_response(options, data)
                if content.get('sn_error'):
                    return {'result': content['sn_error']['error_msg'], 'code': -1}
                else:
                    totalpage = int(content['sn_head']['pageTotal'])
                    res['result'] += content['sn_body']['queryPlantInfo']
                pageno += 1
        i = 0
        for r in res['result']:
            res['map'][r['coCode']] = i
            i += 1
        return res

    def sychronize_orders(self, order_ids=False, shop_type=False, last_time=False):
        plate_list = self.get_plate()
        if plate_list['code'] < 0:
            return plate_list
        pageno = 1
        totalpage = 999999
        res = {'result': [], 'code': 0}
        options = {'appKey': self.appKey.encode('utf-8'),
                   'access_token': self.access_token,
                   'appMethod': SuningAPI.METHOD_LIST['sychronize_items'],
                   'versionNo': 'v1.2',
                   'format': 'json',
                   'appRequestTime': self.get_timestamp(),
                   'Content-type': 'application/json;charset=UTF-8',
                   "Cache-Control": "no-cache",
                   "Connection": "Keep-Alive"}
        while pageno <= totalpage:
            data = {
                "sn_request": {
                    "sn_body": {
                        "purchaseOrder": {
                            "pageNo": str(pageno),
                            "pageSize": "50",
                        }
                    }
                }
            }
            if last_time:
                data["sn_request"]["sn_body"]["purchaseOrder"]["startDate"] = last_time
            if order_ids:
                data["sn_request"]["sn_body"]["purchaseOrder"]["orderCode"] = order_ids[0]
            options['signInfo'] = self.sign(options=options, data=data)
            content = self.get_response(options, data)
            if content.get('sn_error'):
                return {'result': content['sn_error']['error_msg'], 'code': -1}
            else:
                totalpage = int(content['sn_head']['pageTotal'])
                for order in content['sn_body']['purchaseOrder']:
                    plate = plate_list['result'][plate_list['map'][order['coCode']]]
                    details = []
                    confirm_need = False
                    for detail in order['orderDetail']:
                        if detail.get('supplierConfirm', False) == 'X':
                            confirm_need = True
                        details.append({'price': float(detail['unitPrice']),
                                        'deliverCenterId': False,
                                        'deliverCenterName': plate['coDesc'],
                                        'sku_id': detail['supplierProductCode'],
                                        'num': float(detail['orderQty']),
                                        'actualNum': float(detail['orderQty']),
                                        'originalNum': float(detail['orderQty']),
                                        'remark': ""})
                    res['result'].append({'source_code': order['itemCode'],
                                          'order_state': order['orderStatus'],
                                          'order_start_time': order['orderCreateDate'],
                                          'delete_mark': order['orderStatus'] == "50",
                                          'location_province': False,
                                          'location_city': plate['cityName'],
                                          'location_district': False,
                                          'location_details': plate['streetCode'],
                                          'location_mark': plate['postCode'],
                                          'delivery_name': False,
                                          'delivery_phone': False,
                                          'deliverCenterId': False,
                                          'deliverCenterName': plate['coDesc'],
                                          'warehouseName': plate['plantName'],
                                          'confirm_need': confirm_need,
                                          'pur_erp': False,
                                          'details': details})
            pageno += 1
        return res
