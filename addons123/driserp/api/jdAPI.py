# -*- coding: utf-8 -*-
import urllib2
import json
import datetime
import time
import logging

_logger = logging.getLogger(__name__)


class JDAPI(object):
    '''For JD Vendors API'''
    WEB_URL = "https://api.jd.com/routerjson?"
    METHOD_LIST = {'sychronize_info': 'jingdong.vc.item.product.get',
                   'sychronize_orders': 'jingdong.po.list.page.get',
                   'get_order_details': 'jingdong.po.detail.page.get',
                   'order_confirm': 'jingdong.procurement.order.confirm',
                   'sychronize_categories': 'jingdong.vc.item.categories.find',
                   'sychronize_brand': 'jingdong.vc.item.brands.find',
                   'sychronize_items': 'jingdong.vc.item.products.find',
                   'sychronize_return': 'jingdong.vc.return.order.list.page.get',
                   'get_return_detail': 'jingdong.vc.get.return.order.detail',
                   'sychronize_shop': ''}
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
                sign += key + str(options[key]).replace(' ', '')
            else:
                sign += key + options[key]
        sign += self.secret
        return self.md5(sign).upper()

    def check(self):
        return True

    def md5(self, pwd):
        import hashlib
        m = hashlib.md5()
        m.update(pwd)
        return m.hexdigest()

    def get_timestamp(self):
        now = datetime.datetime.utcnow()
        eight_hours = datetime.timedelta(hours=8)
        return (now + eight_hours).strftime('%Y-%m-%d %H:%M:%S')

    def get_response(self, options):
        opt = []
        for option in options.items():
            if isinstance(option[1], dict):
                o_after = []
                for o in option[1].items():
                    o_after.append("\'" + o[0] + "\':\'" + str(o[1]) + "\'")
                opt.append(option[0] + '={' + ','.join(o_after) + '}')
            else:
                opt.append('='.join((option[0], str(option[1]))))
        data = '&'.join(opt)
        req = urllib2.Request(JDAPI.WEB_URL, data, JDAPI.HEADERS)
        try:
            content = urllib2.urlopen(req).read()
            content = json.loads(content)
        except:
            try:
                content = urllib2.urlopen(req).read()
                content = json.loads(content)
            except:
                try:
                    content = urllib2.urlopen(req).read()
                    content = json.loads(content)
                except:
                    return {'code': -1, 'error_response': {'zh_desc': "网络异常，请稍候重试。"}}
        return content

    def sychronize_info(self, code, sku):
        options = {'app_key': self.appKey,
                   'method': JDAPI.METHOD_LIST['sychronize_info'],
                   'access_token': self.access_token,
                   'v': '2.0',
                   'timestamp': self.get_timestamp(),
                   '360buy_param_json': {'wareId': code}}
        options['sign'] = self.sign(options=options)
        content = self.get_response(options)
        if content.get('jingdong_vc_item_product_get_responce'):
            return {'code': 0, 'result': {
                'name': content['jingdong_vc_item_product_get_responce']['jos_result_dto']['single_obj']['name'],
                'brand': content['jingdong_vc_item_product_get_responce']['jos_result_dto']['single_obj']['brand_id'],
                'barcode': content['jingdong_vc_item_product_get_responce']['jos_result_dto']['single_obj']['upc'],
                'category': content['jingdong_vc_item_product_get_responce']['jos_result_dto']['single_obj']['cid1'],
                'url': 'http://item.jd.com/%s.html' % sku,
                'purchase_price': content['jingdong_vc_item_product_get_responce']['jos_result_dto']['single_obj'][
                    'purchase_price'],
                'member_price': content['jingdong_vc_item_product_get_responce']['jos_result_dto']['single_obj'][
                    'member_price'],
                'market_price': content['jingdong_vc_item_product_get_responce']['jos_result_dto']['single_obj'][
                    'market_price'],
            }}
        else:
            return {'code': -1, 'result': content['error_response']['zh_desc']}

    def sychronize_orders(self, order_ids=False, shop_type=False, last_time=False):
        totalPage = 99999
        pageIndex = 1
        page_size = 100
        res = {'code': 0, 'result': [], last_time: ''}
        if order_ids:
            order_ids = ','.join(order_ids)
        while pageIndex <= totalPage:
            options = {'app_key': self.appKey.encode('utf-8'),
                       'access_token': self.access_token,
                       'method': 'jingdong.po.list.page.get',
                       'v': '2.0',
                       'timestamp': self.get_timestamp(),
                       '360buy_param_json': {'pageIndex': str(pageIndex), 'page_size': str(page_size), 'status': 1}}
            if last_time:
                options['360buy_param_json']['createdDateStart'] = last_time
            if order_ids:
                options['360buy_param_json']['orderIds'] = order_ids
            else:
                options['360buy_param_json']['states'] = '0,2,5,6,7,8,10,11,12,15,16'
            options['sign'] = self.sign(options=options)
            content = self.get_response(options)
            if content.get('jingdong_po_list_page_get_responce'):
                pageIndex += 1
                totalPage = content['jingdong_po_list_page_get_responce']['orderResultDto']['totalPage']
                if totalPage == 0:
                    return {'code': -1, 'result': u"未查到订单 %s 订单信息" % order_ids}
                for po in content['jingdong_po_list_page_get_responce']['orderResultDto']['purchaseOrderList']:
                    details = self.get_order_details(str(po['orderId']))
                    if not details['code'] == 0:
                        return details
                    if po['status'] == 0:
                        order_step = 0
                    elif po['state'] in (3,):
                        order_step = 2
                    elif po['state'] in (8, 2, 5):
                        order_step = 1
                    else:
                        order_step = -1
                    res['result'].append({'source_code': unicode(po['orderId']),
                                          'order_state': po['stateName'],
                                          'order_step': order_step,
                                          'delete_mark': po['status'] == 0,
                                          'location_province': False,
                                          'location_city': False,
                                          'location_district': False,
                                          'location_details': po['address'],
                                          'location_mark': po['deliverCenterName'],
                                          'delivery_name': po['receiverName'],
                                          'delivery_phone': po['warehousePhone'],
                                          'deliverCenterId': po['deliverCenterId'],
                                          'deliverCenterName': po['deliverCenterName'],
                                          'confirm_need': (po['isCanConfirm'] == 'true'),
                                          'pur_erp': po.get('purchaserName', False),
                                          'details': details['result'],
                                          'order_start_time': datetime.datetime.strptime(
                                              time.strftime("%Y-%m-%d %H:%M:%S",
                                                            time.localtime(int(po['createdDate']) / 1000)),
                                              '%Y-%m-%d %H:%M:%S'),
                                          'order_end_time': datetime.datetime.strptime(
                                              time.strftime("%Y-%m-%d %H:%M:%S",
                                                            time.localtime(int(po['completeDate']) / 1000)),
                                              '%Y-%m-%d %H:%M:%S') if po.get('completeDate', False) else False})
            else:
                return {'code': -1, 'result': content['error_response']['zh_desc']}
        res['last_time'] = res['result'][-1]['order_start_time']
        return res

    def get_order_details(self, orderId, pageIndex=1, pageSize=100, shop_type=False):
        recordCount = 99999
        rcount = 0
        res = {'code': 0, 'result': []}
        while rcount <= recordCount:
            options = {'app_key': self.appKey.encode('utf-8'),
                       'access_token': self.access_token,
                       'method': JDAPI.METHOD_LIST['get_order_details'],
                       'v': '2.0',
                       'timestamp': self.get_timestamp(),
                       '360buy_param_json': {'orderId': orderId.encode('utf-8'),
                                             'pageIndex': str(pageIndex),
                                             'page_size': str(pageSize)}}
            options['sign'] = self.sign(options=options)
            content = self.get_response(options)
            if content.get('jingdong_po_detail_page_get_responce'):
                rcount += pageSize
                recordCount = content['jingdong_po_detail_page_get_responce']['detailResultDto']['recordCount']
                for po in content['jingdong_po_detail_page_get_responce']['detailResultDto']['allocationDetailList']:
                    res['result'].append({'price': float(po['purchasePrice']),
                                          'deliverCenterId': po['deliverCenterId'],
                                          'deliverCenterName': po['deliverCenterName'],
                                          'sku_id': po['purchaseWareProperty']['wareId'],
                                          'num': float(po['confirmNum']),
                                          'actualNum': float(po['actualNum']),
                                          'originalNum': po.get('originalNum', 0),
                                          'remark': po.get('remark', False)})
            else:
                return {'code': -1, 'result': content['error_response']['zh_desc']}
        return res

    def order_confirm(self, orderId, wareId, deliverCenterId, confirmNum, deliveryTime=None):
        options = {'app_key': self.appKey.encode('utf-8'),
                   'access_token': self.access_token,
                   'method': JDAPI.METHOD_LIST['order_confirm'],
                   'v': '2.0',
                   'timestamp': self.get_timestamp(),
                   '360buy_param_json': {'orderId': orderId.encode('utf-8'),
                                         'wareId': ','.join(wareId),
                                         'deliverCenterId': ','.join(deliverCenterId),
                                         'confirmNum': ','.join(confirmNum)}}
        if deliveryTime:
            options['360buy_param_json']['deliveryTime'] = str(deliveryTime)
        options['sign'] = self.sign(options=options)
        # content = self.get_response(options)
        # return content['result']
        return {'code': 0}

    def sychronize_categories(self):
        options = {'app_key': self.appKey.encode('utf-8'),
                   'access_token': self.access_token,
                   'method': JDAPI.METHOD_LIST['sychronize_categories'],
                   'v': '2.0',
                   'timestamp': self.get_timestamp()}
        options['sign'] = self.sign(options=options)
        content = self.get_response(options)
        if content.get('jingdong_vc_item_categories_find_responce'):
            return {'result': content['jingdong_vc_item_categories_find_responce']['jos_result_dto']['result'],
                    'code': 0}
        else:
            return {'result': content['error_response']['zh_desc'], 'code': -1}

    def sychronize_brand(self):
        options = {'app_key': self.appKey.encode('utf-8'),
                   'access_token': self.access_token,
                   'method': JDAPI.METHOD_LIST['sychronize_brand'],
                   'v': '2.0',
                   'timestamp': self.get_timestamp()}
        options['sign'] = self.sign(options=options)
        content = self.get_response(options)
        if content.get('jingdong_vc_item_brands_find_responce'):
            return {'result': content['jingdong_vc_item_brands_find_responce']['jos_result_dto']['result'],
                    'code': 0}
        else:
            return {'result': content['error_response']['zh_desc'], 'code': -1}

    def sychronize_items(self):
        result = {'code': 0, 'result': []}
        brands = self.sychronize_brand()
        categorys = self.sychronize_categories()
        if brands['code'] < 0:
            return {'result': brands['result'], 'code': -1}
        if categorys['code'] < 0:
            return {'result': categorys['result'], 'code': -1}
        for brand in brands['result']:
            for category in categorys['result']:
                options = {'app_key': self.appKey.encode('utf-8'),
                           'access_token': self.access_token,
                           'method': JDAPI.METHOD_LIST['sychronize_items'],
                           'v': '2.0',
                           '360buy_param_json': {'brand_id': brand['id'],
                                                 'category_id': category['id'],
                                                 'offset': '0', 'page_size': '0'},
                           'timestamp': self.get_timestamp()}
                options['sign'] = self.sign(options=options)
                content = self.get_response(options)
                if content.get('jingdong_vc_item_products_find_responce'):
                    count = content['jingdong_vc_item_products_find_responce']['jos_result_dto']['count']
                    options = {'app_key': self.appKey.encode('utf-8'),
                               'access_token': self.access_token,
                               'method': JDAPI.METHOD_LIST['sychronize_items'],
                               'v': '2.0',
                               '360buy_param_json': {'brand_id': brand['id'],
                                                     'category_id': category['id'],
                                                     'offset': '0', 'page_size': str(count)},
                               'timestamp': self.get_timestamp()}
                    # options['360buy_param_json'] = {'brand_id': brand.encode('utf-8'),
                    #                                 'category_id': category.encode('utf-8'),
                    #                                 'offset': '0', 'page_size': str(count)},
                    options['sign'] = self.sign(options=options)
                    content = self.get_response(options)
                    if content.get('jingdong_vc_item_products_find_responce'):
                        for item in content['jingdong_vc_item_products_find_responce']['jos_result_dto']['result']:
                            active_status = 'on' if item['sale_state'] == 1 else 'off'
                            it = self.sychronize_info(str(item['ware_id']), str(item['ware_id']))
                            if it['code'] < 0:
                                return it
                            result['result'].append({'ware_id': str(item['ware_id']),
                                                     'sku': str(item['ware_id']),
                                                     'active_status': active_status,
                                                     'name': it['result']['name'],
                                                     'brand': it['result']['brand'],
                                                     'barcode': it['result']['barcode'],
                                                     'category': it['result']['category'],
                                                     'url': it['result']['url'],
                                                     'purchase_price': it['result']['purchase_price'],
                                                     'member_price': it['result']['member_price'],
                                                     'market_price': it['result']['market_price']})
                    else:
                        return {'result': content['error_response']['zh_desc'], 'code': -1}
                else:
                    return {'result': content['error_response']['zh_desc'], 'code': -1}
        return result

    def sychronize_return(self, pageSize=100, pageIndex=1, last_time=False):
        recordCount = 99999
        nowrec = 0
        res = {'code': 0, 'result': []}
        while nowrec < recordCount:
            options = {'app_key': self.appKey.encode('utf-8'),
                       'access_token': self.access_token,
                       'method': JDAPI.METHOD_LIST['sychronize_return'],
                       'v': '2.0',
                       '360buy_param_json': {'pageSize': pageSize,
                                             'pageIndex': pageIndex},
                       'timestamp': self.get_timestamp()}
            if last_time:
                options['360buy_param_json']['createDateBegin'] = last_time
            options['sign'] = self.sign(options=options)
            content = self.get_response(options)
            if content.get('jingdong_vc_return_order_list_page_get_responce'):
                recordCount = content['jingdong_vc_return_order_list_page_get_responce']['roResultDto']['recordCount']
                for line in content['jingdong_vc_return_order_list_page_get_responce']['roResultDto']['roDtoList']:
                    details = self.get_return_detail(str(line['returnId']))
                    if not details['code'] == 0:
                        return details
                    out_time = datetime.datetime.fromtimestamp(line['outStoreRoomDate'] / 1000) if line.get(
                        'outStoreRoomDate') else False
                    res['result'].append({'name': line['returnId'],
                                          'provider_code': line['providerCode'],
                                          'provider_name': line['providerName'],
                                          'from_place': line['fromDeliverCenterName'],
                                          'to_place': line['toDeliverCenterName'],
                                          'order_state': line['returnStateName'],
                                          'from_address': line['wareHouseAddress'],
                                          'from_phone': line['wareHouseCell'],
                                          'from_name': line['wareHouseContact'],
                                          'stock_name': line['stockName'],
                                          'out_time': out_time,
                                          'details': details['result']})
            else:
                return {'result': content['error_response']['zh_desc'], 'code': -1}
            nowrec += pageSize
            pageIndex += 1
        return res

    def get_return_detail(self, returnid):
        res = {'code': 0, 'result': []}
        options = {'app_key': self.appKey.encode('utf-8'),
                   'access_token': self.access_token,
                   'method': JDAPI.METHOD_LIST['get_return_detail'],
                   'v': '2.0',
                   '360buy_param_json': {'returnId': returnid},
                   'timestamp': self.get_timestamp()}
        options['sign'] = self.sign(options=options)
        content = self.get_response(options)
        if content.get('jingdong_vc_get_return_order_detail_responce'):
            for line in content['jingdong_vc_get_return_order_detail_responce']['detailResultDto']['detailDtoList']:
                res['result'].append({'item_id': line['wareId'],
                                      'return_price': line['returnsPrice'],
                                      'return_num': line['returnsNum'],
                                      'return_actual': line['factNum']})
            pass
        else:
            return {'result': content['error_response']['zh_desc'], 'code': -1}
        return res

    def sychronize_shop(self):
        return {'code': 0, 'result': {'code': False,
                                      'name': False,
                                      'shop_type': 'vendor'}}
