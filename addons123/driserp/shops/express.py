# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EcpsExpress(models.Model):
    _name = "ecps.express"

    name = fields.Char(string=u'名称', required=True)
    code = fields.Char(string=u'编码', required=True)
    active = fields.Boolean(string=u'Active', default=True)
    pdf_id = fields.Char(string=u'面单模版')
    express_api = fields.Char(string=u'电子面单接口', required=True)
    code_api = fields.Char(string=u'单号获取接口')
    appKey = fields.Char(string=u'appKey', required=True)
    EBusinessID = fields.Char(string=u'电商ID', required=True)

    # JD
    jd_code = fields.Char(string=u'京东编码')
    jd_name = fields.Char(string=u'京东名称')


class EcpsExpressConfig(models.Model):
    _name = "ecps.express.config"

    sequence = fields.Integer(string=u'优先度')
    express_id = fields.Many2one('ecps.express', string=u'快递公司', required=True)
    province_ids = fields.Many2many('res.province', string=u'省')
    city_ids = fields.Many2many('res.city', string=u'市')
    district_ids = fields.Many2many('res.district', string=u'县')
    shop_id = fields.Many2one('ecps.shop', string=u'店铺')
    weight = fields.Float(string=u'重量')
    weight_condition = fields.Selection([('bigger', '大于等于'),
                                         ('lighter', '小于等于'),
                                         ('none', '不启用')], string=u'重量条件')

    def _defaults_sequence(self, cr, uid, context):
        menu = self.search_read(cr, uid, [(1, "=", 1)], ["sequence"], limit=1, order="sequence DESC", context=context)
        return menu and menu[0]["sequence"] or 0

    _defaults = {
        'sequence': _defaults_sequence
    }

    _order = "sequence"


class EcpsBox(models.Model):
    _name = "ecps.box"

    name = fields.Char(string=u'标题')

    wave_id = fields.Many2one('stock.picking.wave', string=u'波次')
    picking_id = fields.Many2one('stock.picking', string=u'拣货单')
    order_line_id = fields.Many2one('sale.order.line', string=u'销售订单行')
    order_id = fields.Many2one('sale.order', string=u'销售订单', related='order_line_id.order_id')
    to_place = fields.Char(string=u'发往')
    address = fields.Char(string=u'地址')
    contact_name = fields.Char(string=u'联系人姓名')
    contact_phone = fields.Char(string=u'联系人电话')
    order_code = fields.Char(string=u'订单号', related='order_id.source_code')
    order_date = fields.Date(string=u'订购日期')
    barcode = fields.Char(string=u'条码')
    item_id = fields.Char(string=u'产品名称')
    box_no = fields.Integer(string=u'箱号')
    box_num = fields.Integer(string=u'单次总箱数')

    origin_num = fields.Float(string=u'采购数量')
    inner_num = fields.Float(string=u'箱内数量')

    printed = fields.Boolean(string=u'已打印', default=False)

    @api.one
    def get_html(self):
        a = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
        	<meta charset="UTF-8">
        	<title>东方万佳</title>
        	<style type="text/css">
        *{ margin: 0; padding: 0;}
        abbbad %s %f
            mkn
        ;;s
        """ % ('a', 1.1)
        s = """<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<title>东方万佳</title>
	<style type="text/css">
*{ margin: 0; padding: 0;}
body,html,div,table,tr,td,th,thead,tbody,font,em{font-size: 18px; color: #333; border: 0; font-style: normal; font-family:"微软雅黑";}
.table{ width:800px; margin:15px auto;}
.table table{width: 100%; border-top: 3px solid #333; border-left: 3px solid #333;}
.table table tbody td,.table table tbody th,.table table thead th{border-bottom: 3px solid #333;border-right: 3px solid #333; padding: 15px;}
.table table thead th font{ font-size:24px; font-weight: bold;}
.table table thead th{ position: relative; }
.table table thead th font.num{ font-size:48px; position: absolute; right:20%; top:0;}

.table table tbody th,.table table tbody td.td1,.table table tbody td.tda{ font-size: 20px; font-weight:bold; }
.table table thead th font{margin-right: 15px;}
.table table tbody td.td1{ padding-left: 15px;}
.table table tbody td.td2{ border-right: none; }
.table table tbody .thnum,.table table tbody td.tda{ width:15%;}
.table table tbody .thnum{text-align: center;}
.table table tbody td font,.tda em{margin: 0 5px;}

	</style>
</head>
<body>
	<div class="table">
		<table cellpadding="0" cellspacing="0" border="0">
			<thead>
				<tr>
					<th colspan="5">
						<font>""" + self.name.encode('utf-8') + """</font>
					</th>
				</tr>
			</thead>
			<tbody>
				<tr>
					<td class="td1">发往:</td>
					<td colspan="4">
						<font>京东</font>
						<font>上海</font>
						<font>百货服装仓B3库</font>
					</td>
				</tr>
				<tr>
					<td class="td1">地址:</td>
					<td colspan="4">江苏省昆山市陆家镇金阳东路近泗桥路普洛斯物流园区毛慧 021-33355952,13381705619</td>
				</tr>
				<tr>
					<td class="td1">订单号:</td>
					<td class="td2">19421802</td>
					<td class="tda">订购日期</td>
					<td>2016.9.20</td>
					<td></td>
				</tr>
				<tr>
					<th class="thnum">商品编码</th>
					<th colspan="2">商品名称</th>
					<th class="thnum">采购数量</th>
					<th class="thnum">箱内数量</th>
				</tr>
				<tr class="tr1">
					<td class="thnum">1945624</td>
					<td colspan="2">
						绿之源 香樟木球樟木球块 书桌衣柜
						防霉防蛀虫去除甲醛樟脑丸20粒装(1.8cm)
					</td>
					<td class="thnum">450</td>
					<td class="thnum">300</td>
				</tr>
				<tr>
					<td></td>
					<td class="td2"><b>本批次货物</b></td>
					<td class="tda">共计<em>3</em>箱</td>
					<td></td>
					<td></td>
				</tr>
			</tbody>
		</table>
	</div>
</body>
</html>"""
            # % (self.name, self.to_place, self.address + " " + self.contact_name + " " + self.contact_phone, self.order_code, "", self.barcode, self.item_id, self.origin_num, self.inner_num, self.box_num)
        return s
