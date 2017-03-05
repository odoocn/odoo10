# -*- coding: utf-8 -*-
import urllib2
import json
import datetime
import logging


class JDPOPAPI(object):
    '''For JD Vendors API'''
    WEB_URL = "https://api.jd.com/routerjson?"
    METHOD_LIST = {'sychronize_price': 'jingdong.ware.price.get',
                   'sychronize_info': '360buy.ware.get',
                   'sychronize_orders': {'fbp': '360buy.order.fbp.search',
                                         'lbp': '360buy.order.search',
                                         'sop': '360buy.order.search',
                                         'sopl': '360buy.order.search'},
                   'order_confirm': 'jingdong.procurement.order.confirm',
                   'sychronize_categories': '360buy.warecats.get',
                   'sychronize_brand': 'jingdong.pop.vender.cener.venderBrand.query',
                   'sychronize_items': '360buy.ware.listing.get',
                   'sychronize_return': '',
                   'get_return_detail': '',
                   'sychronize_shop': 'jingdong.seller.vender.info.get'}
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
                    o_after.append('"' + o[0] + '":"' + str(o[1]) + '"')
                opt.append(option[0] + '={' + ','.join(o_after) + '}')
            else:
                opt.append('='.join((option[0], str(option[1]))))
        data = '&'.join(opt)
        req = urllib2.Request(JDPOPAPI.WEB_URL, data, JDPOPAPI.HEADERS)
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

    def sychronize_categories(self):
        result = {'code': 0, 'result': []}
        options = {'app_key': self.appKey.encode('utf-8'),
                   'access_token': self.access_token,
                   'method': JDPOPAPI.METHOD_LIST['sychronize_categories'],
                   'v': '2.0',
                   'timestamp': self.get_timestamp(),
                   '360buy_param_json': {'fields': 'id,lev,name'}}
        options['sign'] = self.sign(options=options)
        content = self.get_response(options)
        if content.get('ware_category_search_response'):
            for cat in content['ware_category_search_response']['item_cats']:
                if cat['lev'] == 3:
                    result['result'].append({'id': str(cat['id']), 'name': cat['name']})
            return result
        else:
            return {'result': content['error_response']['zh_desc'], 'code': -1}

    def sychronize_brand(self):
        result = {'code': 0, 'result': []}
        options = {'app_key': self.appKey.encode('utf-8'),
                   'access_token': self.access_token,
                   'method': JDPOPAPI.METHOD_LIST['sychronize_brand'],
                   'v': '2.0',
                   'timestamp': self.get_timestamp()}
        options['sign'] = self.sign(options=options)
        content = self.get_response(options)
        if content.get('jingdong_pop_vender_cener_venderBrand_query_responce'):
            for r in content['jingdong_pop_vender_cener_venderBrand_query_responce']['brandList']:
                result['result'].append({'id': str(r['erpBrandId']), 'name': r['brandName']})
            return result
        else:
            return {'result': content['error_response']['zh_desc'], 'code': -1}

    def sychronize_items(self):
        listing = self.sychronize_listing_items()
        if listing['code'] < 0:
            return listing
        delisting = self.sychronize_delisting_items()
        if delisting['code'] < 0:
            return delisting
        return {'code': 0, 'result': listing['result'] + delisting['result']}

    def sychronize_listing_items(self, pageSize=100, pageIndex=1):
        recordCount = 99999
        nowrec = 0
        res = {'code': 0, 'result': []}
        while nowrec < recordCount:
            options = {'app_key': self.appKey.encode('utf-8'),
                       'access_token': self.access_token,
                       'method': '360buy.ware.listing.get',
                       'v': '2.0',
                       '360buy_param_json': {'page': pageIndex,
                                             'page_size': pageSize,
                                             'end_modified': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                             'start_modified': "1980-01-01 10:00:00",
                                             'fields': 'ware_id'},
                       'timestamp': self.get_timestamp()}
            options['sign'] = self.sign(options=options)
            content = self.get_response(options)
            if content.get('ware_listing_get_response'):
                recordCount = int(content['ware_listing_get_response']['total'])
                nowrec += pageSize
                pageIndex += 1
                for r in content['ware_listing_get_response']['ware_infos']:
                    item = self.sychronize_info(str(r['ware_id']), False)
                    if item['code'] < 0:
                        return item
                    for sku in item['result']:
                        res['result'].append({'ware_id': str(r['ware_id']), 'active_status': 'on',
                                              'name': sku['name'],
                                              'brand': sku['brand'],
                                              'category': sku['category'],
                                              'weight': sku['weight'],
                                              'url': sku['url'],
                                              'purchase_price': sku['purchase_price'],
                                              'member_price': sku['member_price'],
                                              'market_price': sku['market_price'],
                                              'barcode': sku['barcode'],
                                              'sku': str(sku['sku'])})
            else:
                return {'result': content['error_response']['zh_desc'], 'code': -1}
        return res

    def sychronize_delisting_items(self, pageSize=100, pageIndex=1):
        recordCount = 99999
        nowrec = 0
        res = {'code': 0, 'result': []}
        while nowrec < recordCount:
            options = {'app_key': self.appKey.encode('utf-8'),
                       'access_token': self.access_token,
                       'method': '360buy.ware.delisting.get',
                       'v': '2.0',
                       '360buy_param_json': {'page': pageIndex,
                                             'page_size': pageSize,
                                             'end_modified': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                             'start_modified': "1980-01-01 10:00:00",
                                             'fields': 'ware_id'},
                       'timestamp': self.get_timestamp()}
            options['sign'] = self.sign(options=options)
            content = self.get_response(options)
            if content.get('ware_delisting_get_response'):
                recordCount = int(content['ware_delisting_get_response']['total'])
                nowrec += pageSize
                pageIndex += 1
                for r in content['ware_delisting_get_response']['ware_infos']:
                    item = self.sychronize_info(str(r['ware_id']), False)
                    if item['code'] < 0:
                        return item
                    for sku in item['result']:
                        res['result'].append({'ware_id': str(r['ware_id']), 'active_status': 'off',
                                              'name': sku['name'],
                                              'brand': sku['brand'],
                                              'weight': sku['weight'],
                                              'category': sku['category'],
                                              'barcode': sku['barcode'],
                                              'url': sku['url'],
                                              'purchase_price': sku['purchase_price'],
                                              'member_price': sku['member_price'],
                                              'market_price': sku['market_price'],
                                              'sku': str(sku['sku'])})
            else:
                return {'result': content['error_response']['zh_desc'], 'code': -1}
        return res

    def sychronize_info(self, code, sku):
        options = {'app_key': self.appKey,
                   'access_token': self.access_token,
                   'method': JDPOPAPI.METHOD_LIST['sychronize_info'],
                   'v': '2.0',
                   'timestamp': self.get_timestamp(),
                   '360buy_param_json': {'ware_id': code}}
        options['sign'] = self.sign(options=options)
        content = self.get_response(options)
        if content.get('ware_get_response'):
            if sku:
                for s in content['ware_get_response']['ware']['skus']:
                    if sku == str(s['sku_id']):
                        return {'code': 0, 'result': {
                            'name': content['ware_get_response']['ware']['title'] + "(%s)" % s['color_value'],
                            'brand': str(content['ware_get_response']['ware']['brand_id']),
                            'barcode': s['outer_id'],
                            'category': str(content['ware_get_response']['ware']['cid']),
                            'weight': float(content['ware_get_response']['ware']['weight']),
                            'url': "http://item.jd.com/" + sku + ".html",
                            'purchase_price': content['ware_get_response']['ware']['cost_price'],
                            'member_price': s['jd_price'],
                            'market_price': s['market_price'],
                            'active_status': 'on' if s['status'] == 'VALID' else 'off',
                            }}
                return {'code': -1, 'result': "sku error"}
            skus = []
            for s in content['ware_get_response']['ware']['skus']:
                skus.append({'sku': str(s['sku_id']), 'name': content['ware_get_response']['ware']['title'] + "(%s)" % s['color_value'],
                             'brand': str(content['ware_get_response']['ware']['brand_id']),
                             'barcode': s['outer_id'],
                             'category': str(content['ware_get_response']['ware']['cid']),
                             'weight': float(content['ware_get_response']['ware']['weight']),
                             'url': "http://item.jd.com/" + str(s['sku_id']) + ".html",
                             'purchase_price': content['ware_get_response']['ware']['cost_price'],
                             'member_price': s['jd_price'],
                             'market_price': s['market_price'],
                             'active_status': 'on' if s['status'] == 'VALID' else 'off'})
            return {'code': 0, 'result': skus}
        else:
            return {'code': -1, 'result': content['error_response']['zh_desc']}

    def sychronize_orders(self, order_ids=False, pageIndex=1, page_size=100, shop_type=False, last_time=False):
        if shop_type == 'fbp' and not order_ids:
            return self.sychronize_order_fbp()
        elif shop_type == 'fbp' and order_ids:
            return self.sychronize_order_fbp_only(order_ids=order_ids)
        elif not order_ids:
            return self.sychronize_order_other(shop_type, last_time)
        elif order_ids:
            return self.sychronize_order_other_only(order_ids=order_ids)

    def sychronize_order_other(self, shop_type, last_time, pageIndex=1, page_size=100):
        totalrec = 99999
        nowrec = 0
        res = {'code': 0, 'result': [], 'last_time': ''}
        order_state = "WAIT_SELLER_STOCK_OUT,WAIT_GOODS_RECEIVE_CONFIRM,WAIT_SELLER_DELIVERY"
        if shop_type in ('lbp', 'sopl'):
            order_state += "SEND_TO_DISTRIBUTION_CENER,DISTRIBUTION_CENTER_RECEIVED,RECEIPTS_CONFIRM"
        while nowrec < totalrec:
            options = {'app_key': self.appKey.encode('utf-8'),
                       'access_token': self.access_token,
                       'method': '360buy.order.search',
                       'v': '2.0',
                       'timestamp': self.get_timestamp(),
                       '360buy_param_json': {'end_date': self.get_timestamp(),
                                             'order_state': order_state,
                                             'page': str(pageIndex), 'page_size': str(page_size)}}
            if not last_time:
                options['360buy_param_json']['start_date'] = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime(
                                                 "%Y-%m-%d %H:%M:%S")
            else:
                options['360buy_param_json']['start_date'] = last_time
            options['sign'] = self.sign(options=options)
            content = self.get_response(options)
            if content.get('order_search_response'):
                pageIndex += 1
                nowrec += 100
                totalrec = content['order_search_response']['order_search'][
                    'order_total']
                for po in content['order_search_response']['order_search'][
                    'order_info_list']:
                    if po['order_state'] in ('SEND_TO_DISTRIBUTION_CENER',
                                                'DISTRIBUTION_CENTER_RECEIVED',
                                                'WAIT_GOODS_RECEIVE_CONFIRM'):
                        order_step = 1
                    elif po['order_state'] in ('RECEIPTS_CONFIRM', 'FINISHED_L'):
                        order_step = 2
                    else:
                        order_step = 0
                    details = []
                    for line in po['item_info_list']:
                        details.append({'price': line['jd_price'],
                                        'sku_id': line['sku_id'],
                                        'num': float(line['item_total']),
                                        'actualNum': float(line['item_total']),
                                        'originalNum': float(line['item_total']),
                                        'remark': line['sku_name']})
                    if u'北京' in po['consignee_info']['province'] or \
                       u'上海' in po['consignee_info']['province'] or \
                       u'天津' in po['consignee_info']['province'] or \
                       u'重庆' in po['consignee_info']['province']:
                        po['consignee_info']['county'] = po['consignee_info']['city']
                        po['consignee_info']['city'] = po['consignee_info']['province']
                    res['result'].append({'details': details,
                                          'source_code': unicode(po['order_id']),
                                          'order_state': po['order_state'],
                                          'order_step': order_step,
                                          'location_province': po['consignee_info']['province'],
                                          'location_city': po['consignee_info']['city'],
                                          'location_district': po['consignee_info']['county'],
                                          'location_details': po['consignee_info']['full_address'],
                                          'location_mark': "",
                                          'delivery_name': po['consignee_info']['fullname'],
                                          'delivery_phone': po['consignee_info']['mobile'],
                                          'deliverCenterId': False,
                                          'deliverCenterName': False,
                                          'confirm_need': False,
                                          'order_start_time': po['order_start_time'],
                                          'invoice_info': po.get('invoice_info'),
                                          'special_order': po.get('store_order')})
                    res['last_time'] = po['order_start_time']
            else:
                return {'code': -1, 'result': content['error_response']['zh_desc']}
        return res

    def sychronize_order_other_only(self, order_ids):
        res = {'code': 0, 'result': []}
        options = {'app_key': self.appKey.encode('utf-8'),
                   'access_token': self.access_token,
                   'method': '360buy.order.get',
                   'v': '2.0',
                   'timestamp': self.get_timestamp(),
                   '360buy_param_json': {'order_id': order_ids[0]}}
        options['sign'] = self.sign(options=options)
        content = self.get_response(options)
        if content.get('order_get_response'):
            order = content['order_get_response']['order']['orderInfo']
            if order['order_state'] in ('SEND_TO_DISTRIBUTION_CENER',
                                        'DISTRIBUTION_CENTER_RECEIVED',
                                        'WAIT_GOODS_RECEIVE_CONFIRM'):
                order_step = 1
            elif order['order_state'] in ('RECEIPTS_CONFIRM', 'FINISHED_L'):
                order_step = 2
            else:
                order_step = 0
            details = []
            for line in order['item_info_list']:
                details.append({'price': line['jd_price'],
                                'sku_id': line['sku_id'],
                                'num': float(line['item_total']),
                                'actualNum': float(line['item_total']),
                                'originalNum': float(line['item_total']),
                                'remark': line['sku_name']})
            if u'北京' in order['consignee_info']['province'] or \
               u'上海' in order['consignee_info']['province'] or \
               u'天津' in order['consignee_info']['province'] or \
               u'重庆' in order['consignee_info']['province']:
                order['consignee_info']['county'] = order['consignee_info']['city']
                order['consignee_info']['city'] = order['consignee_info']['province']
            res['result'].append({'source_code': unicode(order['order_id']),
                                  'details': details,
                                  'order_state': order['order_state'],
                                  'order_step': order_step,
                                  'location_province': order['consignee_info']['province'],
                                  'location_city': order['consignee_info']['city'],
                                  'location_district': order['consignee_info']['county'],
                                  'location_details': order['consignee_info']['full_address'],
                                  'location_mark': "",
                                  'delivery_name': order['consignee_info']['fullname'],
                                  'delivery_phone': order['consignee_info']['mobile'],
                                  'deliverCenterId': False,
                                  'deliverCenterName': False,
                                  'confirm_need': False,
                                  'order_start_time': order['order_start_time'],
                                  'invoice_info': order['invoice_info'],
                                  'special_order': order['store_order']})
            return res
        else:
            return {'code': -1, 'result': content['error_response']['zh_desc']}

    def sychronize_order_fbp(self, pageIndex=1, page_size=100):
        totalrec = 99999
        nowrec = 0
        res = {'code': 0, 'result': []}
        while nowrec < totalrec:
            options = {'app_key': self.appKey.encode('utf-8'),
                       'access_token': self.access_token,
                       'method': '360buy.order.fbp.search',
                       'v': '2.0',
                       'timestamp': self.get_timestamp(),
                       '360buy_param_json': {'end_date': self.get_timestamp(),
                                             'start_date': (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S"),
                                             'page': str(pageIndex), 'page_size': str(page_size)}}
            options['sign'] = self.sign(options=options)
            content = self.get_response(options)
            if content.get('360buy_order_fbp_search_response'):
                pageIndex += 1
                nowrec += 100
                totalrec = content['360buy_order_fbp_search_response']['orderFbpSearchResponse']['order_search']['order_total']
                for po in content['360buy_order_fbp_search_response']['orderFbpSearchResponse']['order_search']['order_info_list']:
                    order = po['order_info']
                    if order['order_state'] in ('WAIT_SELLER_STOCK_OUT',
                                                'SEND_TO_DISTRIBUTION_CENER',
                                                'DISTRIBUTION_CENTER_RECEIVED',
                                                'WAIT_GOODS_RECEIVE_CONFIRM'):
                        order_step = 1
                    elif order['order_state'] in ('RECEIPTS_CONFIRM', 'FINISHED_L'):
                        order_step = 2
                    else:
                        order_step = 0
                    details = []
                    for line in order['item_info_list']:
                        details.append({'price': line['jd_price'],
                                        'sku_id': line['sku_id'],
                                        'num': float(line['item_total']),
                                        'actualNum': float(line['item_total']),
                                        'originalNum': float(line['item_total']),
                                        'remark': float(line['sku_name'])})
                    res['result'].append({'source_code': unicode(order['order_id']),
                                          'order_state': order['order_state_remark'],
                                          'order_step': order_step,
                                          'location_province': order['consignee_info']['province'],
                                          'location_city': order['consignee_info']['city'],
                                          'location_district': order['consignee_info']['county'],
                                          'location_details': order['consignee_info']['full_address'],
                                          'location_mark': "",
                                          'delivery_name': order['consignee_info']['fullname'],
                                          'delivery_phone': order['consignee_info']['mobile'],
                                          'confirm_need': False})

            else:
                return {'code': -1, 'result': content['error_response']['zh_desc']}
        return res

    def sychronize_order_fbp_only(self, order_ids):
        res = {'code': 0, 'result': []}
        options = {'app_key': self.appKey.encode('utf-8'),
                   'access_token': self.access_token,
                   'method': '360buy.order.fbp.get',
                   'v': '2.0',
                   'timestamp': self.get_timestamp(),
                   '360buy_param_json': {'order_id': order_ids[0]}}
        options['sign'] = self.sign(options=options)
        content = self.get_response(options)
        if content.get('360buy_order_fbp_get_response'):
            order = content['360buy_order_fbp_get_response']['orderFbpGetResponse']['order']['orderInfo']
            if order['order_state'] in ('WAIT_SELLER_STOCK_OUT',
                                        'SEND_TO_DISTRIBUTION_CENER',
                                        'DISTRIBUTION_CENTER_RECEIVED',
                                        'WAIT_GOODS_RECEIVE_CONFIRM'):
                order_step = 1
            elif order['order_state'] in ('RECEIPTS_CONFIRM', 'FINISHED_L'):
                order_step = 2
            else:
                order_step = 0
            details = []
            for line in order['item_info_list']:
                details.append({'price': line['jd_price'],
                                'sku_id': line['sku_id'],
                                'num': float(line['item_total']),
                                'actualNum': float(line['item_total']),
                                'originalNum': float(line['item_total']),
                                'remark': line['sku_name']})
            res['result'].append({'source_code': unicode(order['order_id']),
                                  'order_state': order['order_state_remark'],
                                  'order_step': order_step,
                                  'location_province': order['consignee_info']['province'],
                                  'location_city': order['consignee_info']['city'],
                                  'location_district': order['consignee_info']['county'],
                                  'location_details': order['consignee_info']['full_address'],
                                  'location_mark': "",
                                  'delivery_name': order['consignee_info']['fullname'],
                                  'delivery_phone': order['consignee_info']['mobile'],
                                  'confirm_need': False})
            return res
        else:
            return {'code': -1, 'result': content['error_response']['zh_desc']}

    def sychronize_shop(self):
        result = {'code': 0, 'result': {}}
        options = {'app_key': self.appKey.encode('utf-8'),
                   'access_token': self.access_token,
                   'method': JDPOPAPI.METHOD_LIST['sychronize_shop'],
                   'v': '2.0',
                   'timestamp': self.get_timestamp()}
        options['sign'] = self.sign(options=options)
        content = self.get_response(options)
        if content.get('jingdong_seller_vender_info_get_responce'):
            if content['jingdong_seller_vender_info_get_responce']['vender_info_result']['col_type'] == 0:
                result['result'] = {
                    'code': content['jingdong_seller_vender_info_get_responce']['vender_info_result']['shop_id'],
                    'name': content['jingdong_seller_vender_info_get_responce']['vender_info_result']['shop_name'],
                    'shop_type': 'sop'}
            elif content['jingdong_seller_vender_info_get_responce']['vender_info_result']['col_type'] == 1:
                result['result'] = {
                    'code': content['jingdong_seller_vender_info_get_responce']['vender_info_result']['shop_id'],
                    'name': content['jingdong_seller_vender_info_get_responce']['vender_info_result']['shop_name'],
                    'shop_type': 'fbp'}
            elif content['jingdong_seller_vender_info_get_responce']['vender_info_result']['col_type'] == 2:
                result['result'] = {
                    'code': content['jingdong_seller_vender_info_get_responce']['vender_info_result']['shop_id'],
                    'name': content['jingdong_seller_vender_info_get_responce']['vender_info_result']['shop_name'],
                    'shop_type': 'lbp'}
            elif content['jingdong_seller_vender_info_get_responce']['vender_info_result']['col_type'] == 5:
                result['result'] = {
                    'code': content['jingdong_seller_vender_info_get_responce']['vender_info_result']['shop_id'],
                    'name': content['jingdong_seller_vender_info_get_responce']['vender_info_result']['shop_name'],
                    'shop_type': 'sopl'}
            return result
        else:
            return {'result': content['error_response']['zh_desc'], 'code': -1}
