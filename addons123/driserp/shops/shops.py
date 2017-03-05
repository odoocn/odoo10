# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from addons.driserp.tools.security_log import write_log as log
import datetime
import urllib2
import requests
import json
import time


class ShopsPlate(models.Model):
    _name = "ecps.plate"

    name = fields.Char(string=u'平台', required=True)
    plate_api = fields.Selection([('jd', '京东自营'),
                                  ('jd_pop', '京东POP'),
                                  ('vip', '唯品会供应商'),
                                  ('vip_sandbox', '唯品会沙箱'),
                                  ('taobao', '淘宝'),
                                  ('tb_sandbox', '淘宝沙箱'),
                                  ('yhd', '一号店供应商'),
                                  ('suning', '苏宁易购')], string=u'平台接口', required=True)
    auth_type = fields.Selection([('oauth', 'Oauth2'), ('amzon', '亚马逊')], string=u'授权方式', required=True)
    auth_url = fields.Char(string=u'授权地址', required=True, help="例如：https://member.yhd.com/login/authorize.do?")
    token_url = fields.Char(string=u'token获取地址', help="例如：https://member.yhd.com/login/token.do?")
    refresh_url = fields.Char(string=u'token刷新地址', help="例如：https://member.yhd.com/login/refreshToken.do?")
    secret = fields.Char(string=u'secret')
    appKey = fields.Char(string=u'appKey')
    register_url = fields.Char(string=u'注册路径')
    active = fields.Boolean(string=u'Active', default=True)

    @api.one
    def get_api(self, access_token):
        if self.plate_api == 'jd':
            from addons.driserp.api.jdAPI import JDAPI
            return JDAPI(self.secret.encode('utf-8'), self.appKey.encode('utf-8'), access_token)
        elif self.plate_api == 'jd_pop':
            from addons.driserp.api.jdpopAPI import JDPOPAPI
            return JDPOPAPI(self.secret.encode('utf-8'), self.appKey.encode('utf-8'), access_token)
        elif self.plate_api == 'yhd':
            from addons.driserp.api.yhdAPI import YHDAPI
            return YHDAPI(self.secret.encode('utf-8'), self.appKey.encode('utf-8'), access_token)
        elif self.plate_api == 'taobao':
            from addons.driserp.api.tbAPI import TBAPI
            return TBAPI(self.secret.encode('utf-8'), self.appKey.encode('utf-8'), access_token)
        elif self.plate_api in ('vip', 'vip_sandbox'):
            from addons.driserp.api.vipAPI import VIPAPI
            return VIPAPI(self.secret.encode('utf-8'), self.appKey.encode('utf-8'), access_token)
        else:
            return False


class ShopsUsers(models.Model):
    _inherit = "res.users"

    shop_ids = fields.Many2many('ecps.shop', 'ecps_shop_res_users_rel', string='所在店铺')


class ShopsShop(models.Model):
    _name = "ecps.shop"

    @api.depends('expires_in', 'access_in')
    def check_out(self):
        gmt8 = datetime.timedelta(hours=8)
        if not self.expires_in or datetime.datetime.strptime(self.expires_in, '%Y-%m-%d %H:%M:%S') < datetime.datetime.utcnow():
            self.token_out = True
        else:
            self.token_out = False

    @api.model
    def _default_warehouse(self):
        company = self.env.user.company_id.id
        warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
        return warehouse_ids

    name = fields.Char(string=u'店铺名称', required=True)
    code = fields.Char(string=u'店铺编码')
    access_token = fields.Char(string=u'访问令牌', readonly=True)
    refresh_token = fields.Char(string=u'刷新令牌', readonly=True)
    expires_in = fields.Datetime(string=u'令牌失效时间', readonly=True)
    access_in = fields.Datetime(string=u'令牌授权时间', readonly=True)
    last_sign = fields.Char(string=u'请求签名')
    syn_last = fields.Datetime(string=u'最后同步时间', readonly=True)
    plate_id = fields.Many2one('ecps.plate', string=u'店铺平台', required=True)
    admin_users = fields.Many2many('res.users', 'ecps_shop_res_users_rel', string=u'分管用户')
    items = fields.One2many('ecps.items', 'shop_id', string=u'产品')
    effective = fields.Boolean(string=u'生效', default=True)
    direct_group = fields.Selection([('2B', 'To B'), ('2C', 'To C')], string=u'面向人群', required=True)
    account_id = fields.Many2one('account.analytic.account', string=u'分析帐户')
    partner_id = fields.Many2one('res.partner', string=u'客户对象', required=True)
    uid = fields.Char(string=u'授权用户ID', readonly=True)
    last_refresh = fields.Datetime(string=u'最后同步时间')

    token_out = fields.Boolean(compute=check_out, string=u'令牌失效', default=True)

    location_province = fields.Many2one('res.province', string=u'省')
    location_city = fields.Many2one('res.city', string=u'市')
    location_district = fields.Many2one('res.district', string=u'县')
    location_details = fields.Char(u'详细地址')

    delivery_phone = fields.Char(u'寄件人电话')
    delivery_name = fields.Char(u'寄件人姓名')

    brands = fields.Many2many('ecps.brand', string=u'绑定品牌')
    categories = fields.Many2many('ecps.category', string=u'绑定三级品类')

    express_default = fields.Many2one('ecps.express', string=u'默认快递公司')
    express_config = fields.One2many('ecps.express.config', 'shop_id', string=u'快递配置')

    shop_type = fields.Selection([('sop', 'SOP'),
                                  ('fbp', 'FBP'),
                                  ('lbp', 'LBP'),
                                  ('sopl', 'SOPL'),
                                  ('pop', 'POP'), ('vendor', '供应商')], string=u'商家类型')
    fbp_loc = fields.Many2one('stock.location', string=u'虚拟仓库')
    default_warehouse = fields.Many2one('stock.warehouse', string=u'默认仓库', required=True, default=_default_warehouse)

    @api.multi
    def write_log(self):
        log("JD API: Write Log")

    @api.one
    def compute_sign(self):
        def md5(pwd):
            import hashlib
            m = hashlib.md5()
            m.update(pwd)
            return m.hexdigest()
        self.write({'last_sign': md5(datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') + str(self.id) +
                                 datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))})
        return self.last_sign

    @api.multi
    def syn_shops_auto(self):
        for r in self.search([]):
            try:
                r.refresh_t()
                res = r.refresh_shops()
                if not res['code'] == 0:
                    self.env["error.info"].error_commit(_(res['result']))
            except:
                pass
        return True

    @api.multi
    def syn_order_auto(self):
        warning = ""
        for r in self.search([]):
            res = r.syn_order()
            if not res['code'] == 0:
                for error in res['result']:
                    warning += error['result'] + '\n'
        if warning:
            self.env["error.info"].error_commit(_(warning))
        return True

    @api.multi
    def syn_return_auto(self):
        for r in self.search([]):
            res = r.syn_return()
            if isinstance(res, dict):
                return self.env["error.info"].error_commit(_(res['result']))
            else:
                return True

    @api.multi
    def syn_shops_by_hand(self):
        res = self.refresh_shops()
        if res['code'] == 0:
            return self.env["tools.alert.dialog"].new_alert(_("完成"))
        else:
            self.env["error.info"].error_commit(_(res['result']))
            return self.env["tools.alert.dialog"].new_alert(_(res['result']))

    @api.multi
    def syn_order_by_hand(self):
        res = self.syn_order()
        if res['code'] == 0:
            return self.env["tools.alert.dialog"].new_alert(_("完成"))
        else:
            warning = ""
            for error in res['result']:
                warning += error['result'] + str('\n')
            self.env["error.info"].error_commit(_(warning))
            return self.env["tools.alert.dialog"].new_alert(_(warning))

    @api.multi
    def syn_return_by_hand(self):
        res = self.syn_return()
        if isinstance(res, dict):
            return self.env["tools.alert.dialog"].new_alert(_(res['result']))
        else:
            return self.env["tools.alert.dialog"].new_alert(_("完成"))

    @api.multi
    def write(self, vals):
        res = super(ShopsShop, self).write(vals)
        if self.shop_type == 'fbp' and not self.fbp_loc:
            imd = self.env['ir.model.data']
            virtual_loc = imd.xmlid_to_res_id('stock.stock_location_locations_virtual')
            self.fbp_loc = self.env['stock.location'].create({'name': u'虚拟仓库',
                                                              'usage': u'internal',
                                                              'location_id': virtual_loc,
                                                              'company_id': False})
        return res

    @api.one
    def get_express(self, order_id, weight_total):
        order = self.env['sale.order'].browse(order_id)
        expresses = self.express_config
        for express in expresses:
            if order.location_province.id in express.province_ids:
                if express.weight_condition == 'none':
                    return express.express_id
                if express.weight_condition == 'lighter' and weight_total <= express.weight:
                    return express.express_id
                if express.weight_condition == 'bigger' and weight_total >= express.weight:
                    return express.express_id
            if order.location_city.id in express.city_ids:
                if express.weight_condition == 'none':
                    return express.express_id
                if express.weight_condition == 'lighter' and weight_total <= express.weight:
                    return express.express_id
                if express.weight_condition == 'bigger' and weight_total >= express.weight:
                    return express.express_id
            if order.location_district.id in express.district_ids:
                if express.weight_condition == 'none':
                    return express.express_id
                if express.weight_condition == 'lighter' and weight_total <= express.weight:
                    return express.express_id
                if express.weight_condition == 'bigger' and weight_total >= express.weight:
                    return express.express_id
        return self.express_default

    @api.multi
    def refresh_shops(self):
        '''更新商店的品类、品牌、商品'''
        if not self.access_token:
            return {'code': -1, 'result': "店铺 %s 未授权" % self.name}
        else:
            link_api = self.plate_id.get_api(access_token=self.access_token.encode('utf-8'))[0]
        # 店铺基本信息
        shop_info = link_api.sychronize_shop()
        if shop_info['code'] == 0:
            if shop_info['result']['code']:
                self.write({'code': shop_info['result']['code']})
            if shop_info['result']['name']:
                self.write({'name': shop_info['result']['name']})
            if shop_info['result']['shop_type']:
                self.write({'shop_type': shop_info['result']['shop_type']})
        else:
            return shop_info
            # raise UserError(_(shop_info['result']))
        # 更新三级品类
        res = link_api.sychronize_categories()
        if res['code'] == 0:
            c_ids = []
            for r in res['result']:
                c = self.env['ecps.category'].search([('code', '=', r['id'])])
                if not c or not r['id']:
                    c_id = self.env['ecps.category'].create({'code': r['id'], 'name': r['name']})
                    c_ids.append(c_id.id)
                else:
                    c_ids.append(c[0].id)
            self.write({'categories': [[6, False, c_ids]]})
        else:
            return res
            # raise UserError(_(res['result']))
        # 更新品牌
        res = link_api.sychronize_brand()
        if res['code'] == 0:
            b_ids = []
            for r in res['result']:
                b = self.env['ecps.brand'].search([('code', '=', r['id'])])
                if not b or not r['id']:
                    b_id = self.env['ecps.brand'].create({'code': r['id'], 'name': r['name']})
                    b_ids.append(b_id.id)
                else:
                    b_ids.append(b[0].id)
            self.write({'brands': [[6, False, b_ids]]})
        else:
            return res
            # raise UserError(_(res['result']))
        # TODO:因接口调用流量限制 更新商品暂停
        # 更新商品
        # res = link_api.sychronize_items()
        # if res['code'] == 0:
        #     for r in res['result']:
        #         item = self.env['ecps.items'].search([('code', '=', r['ware_id']), ('item_sku', '=', r['sku']),
        #                                               ('shop_id', '=', self.id)])
        #         if item:
        #             if r['brand']:
        #                 brand = self.env['ecps.brand'].search([('code', '=', r['brand'])])
        #                 if brand:
        #                     brand = brand.id
        #             else:
        #                 brand = False
        #             if r['category']:
        #                 category = self.env['ecps.category'].search([('code', '=', r['category'])])
        #                 if category:
        #                     category = category.id
        #             else:
        #                 category = False
        #             item.write({'active_status': r['active_status'],
        #                         'name': r['name'],
        #                         'barcode': r['barcode'],
        #                         'weight': r.get('weight', 0),
        #                         'purchase_price': r['purchase_price'],
        #                         'member_price': r['member_price'],
        #                         'market_price': r['market_price'],
        #                         'url': r['url'],
        #                         'brand_id': brand,
        #                         'category_id': category})
        #         else:
        #             if r['brand']:
        #                 brand = self.env['ecps.brand'].search([('code', '=', r['brand'])])
        #                 if brand:
        #                     brand = brand.id
        #             else:
        #                 brand = False
        #             if r['category']:
        #                 category = self.env['ecps.category'].search([('code', '=', r['category'])])
        #                 if category:
        #                     category = category.id
        #             else:
        #                 category = False
        #             item = self.env['ecps.items'].create({'shop_id': self.id, 'code': r['ware_id'],
        #                                                   'item_sku': r['sku'],
        #                                                   'active_status': r['active_status'],
        #                                                   'plate_id': self.plate_id.id,
        #                                                   'name': r['name'],
        #                                                   'weight': r.get('weight', 0),
        #                                                   'barcode': r['barcode'],
        #                                                   'purchase_price': r['purchase_price'],
        #                                                   'member_price': r['member_price'],
        #                                                   'market_price': r['market_price'],
        #                                                   'url': r['url'],
        #                                                   'brand_id': brand,
        #                                                   'category_id': category
        #                                                   })
        #         self.env.cr.commit()
        # else:
        #     return res
            # raise UserError(_(res['result']))
        return {'code': 0}

    @api.multi
    def syn_order(self):
        """
            同步订单
        """
        # self.refresh_shops()
        syn_res = self.env['sale.order'].syn_orders(shop_id=self.id)
        return_result = {'code': 0 if syn_res['code'] == 0 else -1,
                         'result': syn_res['result'] if syn_res['code'] != 0 else []}
        if not self.access_token:
            return {'code': -1, 'result': _("店铺 %s 未授权") % self.name}
        else:
            link_api = self.plate_id.get_api(access_token=self.access_token.encode('utf-8'))[0]
        result = link_api.sychronize_orders(shop_type=self.shop_type, last_time=self.last_refresh)
        if result['code'] >= 0:
            for res in result['result']:
                if not self.env['sale.order'].search([('source_code', '=', res['source_code']),
                                                      ('source_shop', '=', self.id)]) and not res['delete_mark']:
                    weight_total = 0
                    order = self.env['sale.order'].create({'location_province': self.env['res.province'].get_province(res['location_province']),
                                                           'location_city': self.env['res.city'].get_city(res['location_city']),
                                                           'location_district': self.env['res.district'].get_district(res['location_district']),
                                                           'location_details': res['location_details'],
                                                           'location_mark': res['location_mark'],
                                                           'source_code': res['source_code'],
                                                           'source_shop': self.id,
                                                           'warehouse_id': self.default_warehouse.id,
                                                           'order_state': res['order_state'],
                                                           'order_step': res['order_step'],
                                                           'partner_id': self.partner_id.id,
                                                           'direct_group': self.direct_group,
                                                           'project_id': self.account_id.id,
                                                           'delivery_name': res['delivery_name'],
                                                           'delivery_phone': res['delivery_phone'],
                                                           'deliverCenterId': res['deliverCenterId'],
                                                           'deliverCenterName': res['deliverCenterName'],
                                                           'confirm_need': res['confirm_need'],
                                                           'return_state': not res['confirm_need'],
                                                           'online_type': 'online',
                                                           'order_start_time': res['order_start_time'],
                                                           'order_end_time': res['order_end_time'],
                                                           'pur_erp': res['pur_erp'],
                                                           'warehouseName': res.get('warehouseName', False),
                                                           'syn_type': True,
                                                           'invoice_info': res.get('invoice_info'),
                                                           'special_order': res.get('special_order')})
                    for line in res['details']:
                        item = self.env['ecps.items'].search([('item_sku', '=', line['sku_id']),
                                                              ('shop_id', '=', self.id)])
                        if not item:
                            return_result['code'] = -1
                            return_result['result'].append(
                                {'code': -1,
                                 'result': _("店铺 %s 下，sku为 %s 的商品不存在。请处理。") % (self.name, line['sku_id'])})
                            order.write({'error_boolean': True})
                            continue
                        weight_total += item.weight
                        product = item.product_id
                        if not product:
                            return_result['code'] = -1
                            return_result['result'].append(
                                {'code': -1,
                                 'result': _("%s 店铺下 %s (%s)的商品还未匹配") % (self.name, item.name, line['sku_id'])})
                            order.write({'error_boolean': True})
                            continue
                            # raise UserError(_("%s 店铺下 %s (%s)的商品还未匹配") % (self.name, item.name, line['sku_id']))
                        self.env['sale.order.line'].create({'order_id': order.id,
                                                            'name': line['remark'] or product.product_tmpl_id.name,
                                                            'product_id': product.id,
                                                            'customer_lead': product.product_tmpl_id.sale_delay,
                                                            'discount': 0,
                                                            # 'invoice_status': 'no',
                                                            'procurement_ids': [],
                                                            'qty_delivered_updateable': True,
                                                            'route_id': False,
                                                            # 'state': 'draft',
                                                            'item_id': item.id,
                                                            'tax_id': [],
                                                            'price_unit': line['price'],
                                                            'product_uom_qty': line['num'],
                                                            'actualNum': line['actualNum'],
                                                            'originalNum': line['originalNum'],
                                                            'product_uom': product.product_tmpl_id.uom_id.id})
                    if order.error_boolean:
                        order.write({'order_step': 0})
                    if order.direct_group == '2C' and not order.error_boolean:
                        order.write({'express_com': self.get_express(order.id, weight_total)[0].id,
                                     'weight_total': weight_total})
                    if order.order_step == 1 and not order.error_boolean:
                        order.action_confirm()
                    if order.order_step < 0 and not order.error_boolean:
                        order.action_cancel()
                    self.env.cr.commit()
            if len(result['result']) > 0:
                self.write({'last_refresh': result['last_time']})
            if result['code'] > 0:
                return_result['result'] += [{'code': -1, 'result': _("订单更新过程中有部分失败")}]
        else:
            return_result = {'code': -1, 'result': [result] + return_result['result']}
        return return_result

    @api.one
    def syn_return(self):
        link_api = self.plate_id.get_api(access_token=self.access_token.encode('utf-8'))[0]
        res = link_api.sychronize_return()
        if not res['code'] == 0:
            return res
            # raise UserError(_(res['result']))
        else:
            for line in res['result']:
                if not self.env['return.order'].search([('name', '=', line['name'])]):
                    r_order = self.env['return.order'].create({
                        'name': line['name'],
                        'provider_code': line['provider_code'],
                        'provider_name': line['provider_name'],
                        'from_place': line['from_place'],
                        'to_place': line['to_place'],
                        'order_state': line['order_state'],
                        'from_address': line['from_address'],
                        'from_phone': line['from_phone'],
                        'from_name': line['from_name'],
                        'stock_name': line['stock_name'],
                        'out_time': line['out_time'],
                        'source_shop': self.id})
                    for o_line in line['details']:
                        item = self.env['ecps.items'].search([('item_sku', '=', o_line['item_id']),
                                                              ('shop_id', '=', self.id)])
                        if not item:
                            return {'code': -1, 'result': _("缺少商品信息，请先同步信息")}
                            # raise UserError(_("缺少商品信息，请先同步信息"))
                        self.env['return.order.line'].create({'return_id': r_order.id,
                                                              'item': item[0].id,
                                                              'return_num': o_line['return_num'],
                                                              'return_price': o_line['return_price'],
                                                              'return_actual': o_line['return_actual']})
        return True

    @api.one
    def refresh_t(self):
        # TODO: move in api
        refresh_url = self.plate_id.refresh_url
        data = {'grant_type': 'refresh_token',
                'client_id': self.plate_id.appKey.encode('utf-8'),
                'client_secret': self.plate_id.secret.encode('utf-8'),
                'refresh_token': self.refresh_token.encode('utf-8')}
        res = requests.post(refresh_url.encode('utf-8'), data)
        content = res.content
        try:
            content.encode('gb2312')
        except:
            pass
        content = json.loads(content)
        gmt8 = datetime.timedelta(hours=8)
        if self.plate_id.plate_api in ('jd', 'jd_pop'):
            if content['code'] == 0:
                access_in = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(content['time']) / 1000))
                return self.write({'access_in': datetime.datetime.strptime(access_in, '%Y-%m-%d %H:%M:%S'),
                                   'access_token': content['access_token'],
                                   'refresh_token': content['refresh_token'],
                                   'expires_in': datetime.datetime.strptime(access_in, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(seconds=content['expires_in'])})
            else:
                raise UserError(content['error_description'])
        elif self.plate_id.plate_api == 'yhd':
            return self.write({'access_in': datetime.datetime.now(),
                               'access_token': content['accessToken'],
                               'refresh_token': content['refreshToken'],
                               'expires_in': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(content['expiresIn']) / 1000))})
        elif self.plate_id.plate_api == 'taobao':
            if res.status_code == 200:
                return self.write({'access_in': datetime.datetime.utcnow(),
                                   'access_token': content['access_token'],
                                   'refresh_token': content['refresh_token'],
                                   'expires_in': datetime.datetime.utcnow() + datetime.timedelta(
                                       seconds=content['expires_in'])})
            else:
                raise UserError(content['error_description'])

    @api.one
    def cancel_t(self):
        self.write({'access_token': False,
                    'refresh_token': False,
                    'expires_in': False,
                    'access_in': False,
                    'last_refresh': False})
        return True


class ShopsItems(models.Model):
    _name = "ecps.items"
    _inherit = ['ir.needaction_mixin']

    name = fields.Char(string=u'平台商品名称')
    plate_id = fields.Many2one('ecps.plate', string=u'平台', required=True)
    shop_id = fields.Many2one('ecps.shop', string=u'平台店铺', required=True)
    item_type = fields.Selection([('2B', '供应商产品'), ('2C', '店铺产品')], related='shop_id.direct_group')
    product_id = fields.Many2one('product.product', string=u'库存产品')
    item_sku = fields.Char(string=u'SKU', required=True)
    code = fields.Char(string=u'商品平台编码')
    barcode = fields.Char(string=u'商品条码')
    weight = fields.Float(string=u'重量(kg)')
    active = fields.Boolean(string=u'上架中', default=True)
    purchase_price = fields.Float(string=u'采购价')
    member_price = fields.Float(string=u'平台价')
    market_price = fields.Float(string=u'市场价')
    url = fields.Char(string=u'网站页面')

    active_status = fields.Selection([('on', '已上架'), ('off', '已下架'), ('del', '已删除')], string=u'商品状态')

    brand_id = fields.Many2one('ecps.brand', string=u'品牌')
    category_id = fields.Many2one('ecps.category', string=u'三级品类')

    _sql_constraints = [
        ('sku_shop_uniq', 'unique (item_sku,shop_id)', u'店铺下商品SKU不可重复')
    ]

    @api.one
    def sychronize_info(self):
        link_api = self.plate_id.get_api(access_token=self.shop_id.access_token)[0]
        result = link_api.sychronize_info(code=self.code.encode('utf-8'), sku=self.item_sku.encode('utf-8'))
        if result['code'] < 0:
            return result
        else:
            if result['result']['brand']:
                brand = self.env['ecps.brand'].search([('code', '=', result['result']['brand'])])
                if brand:
                    brand = brand.id
            else:
                brand = False
            if result['result']['category']:
                category = self.env['ecps.category'].search([('code', '=', result['result']['category'])])
                if category:
                    category = category.id
            else:
                category = False
            self.write({'name': result['result']['name'],
                        'url': result['result']['url'],
                        'active': True,
                        'barcode': result['result']['barcode'],
                        'brand_id': brand,
                        'category_id': category,
                        'weight': result['result'].get('weight', 0),
                        'purchase_price': result['result']['purchase_price'],
                        'member_price': result['result']['member_price'],
                        'market_price': result['result']['market_price']})
        del link_api
        return {'code': 0}

    @api.model
    def _needaction_domain_get(self):
        return [('product_id', '=', False)]


class price_history(models.Model):
    _name = "ecps.item.price"


class EcpsBrand(models.Model):
    _name = "ecps.brand"

    name = fields.Char(string=u'名称')
    code = fields.Char(string=u'商城编码')
    shop_id = fields.Many2many('ecps.shop', string=u'店铺')


class EcpsCategory(models.Model):
    _name = "ecps.category"

    name = fields.Char(string=u'名称')
    code = fields.Char(string=u'商城编码')
    shop_id = fields.Many2many('ecps.shop', string=u'店铺')