# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class transceivers_summary(models.Model):
    _name = "transceivers.summary"
    _description = "Transmit receive Deposit Summary"
    _auto = False
    _rec_name = 'product_id'

    account_date = fields.Date(u'记账日')
    the_receipt = fields.Char(u'凭证摘要')
    send_receive_type = fields.Many2one('type.account.relation', u'收发类型')
    in_qty = fields.Float(u'入库数量', digits=(16,4))
    in_cost_price = fields.Float(u'入库单价', digits=(16,4))
    in_cost_amount = fields.Float(u'入库总额', digits=(16,4))
    out_qty = fields.Float(u'出库数量', digits=(16, 4))
    out_cost_price = fields.Float(u'出库单价', digits=(16, 4))
    out_cost_amount = fields.Float(u'出库总额', digits=(16, 4))
    balance_qty = fields.Float(u'结存数量', digits=(16,4))
    balance_price = fields.Float(u'结存单价', digits=(16,4))
    balance_amount = fields.Float(u'结存成本', digits=(16,4))
    beginning_qty = fields.Float(u'期初数量', digits=(16,4))
    beginning_price = fields.Float(u'结存单价', digits=(16,4))
    beginning_amount = fields.Float(u'期初成本', digits=(16,4))
    product_id = fields.Many2one("product.product", u"存货名称")  # 存货
    uom_id = fields.Many2one('product.uom', u'计量单位')  # 计量单位


    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
    # def search_read(self, cr, uid, domain=None, fields=None, offset=0, limit=None, order=None, context=None):
        if not domain:
            domain = []
        record_ids = self.env['product.detail.account'].search(domain, offset=0, limit=None, order=None, count=False)
        if not record_ids:
            return []
        if len(record_ids) > 1:
            record_string = str(tuple(record_ids))
        else:
            record_string = "(" + str(record_ids[0].id) + ")"

        self.env.cr.execute("""
SELECT
  start_line.product_id as id,
  start_line.product_id as product_id,
  start_line.balance_price as beginning_qty,
  start_line.balance_qty as beginning_price,
  start_line.balance_amount as beginning_amount,
  middle_line.in_cost_price as in_cost_price,
  middle_line.in_qty as in_qty,
  middle_line.in_cost_amount as in_cost_amount,
  middle_line.out_cost_price as out_cost_price,
  middle_line.out_qty as out_qty,
  middle_line.out_cost_amount as out_cost_amount,
  end_line.balance_price as balance_price,
  end_line.balance_qty as balance_qty,
  end_line.balance_amount as balance_amount
FROM (select product_id, balance_qty, balance_price, balance_amount, uom_id
from product_detail_account where id in (select min(id) from product_detail_account WHERE id in %s group by product_id)) start_line
LEFT JOIN (select
  product_id,
  COALESCE(sum(in_qty), 0) as in_qty,
  COALESCE(sum(in_cost_amount)/sum(in_qty), 0) as in_cost_price,
  COALESCE(sum(in_cost_amount), 0) as in_cost_amount,
  COALESCE(sum(out_qty), 0) as out_qty,
  COALESCE(sum(out_cost_amount)/sum(out_qty), 0) as out_cost_price,
  COALESCE(sum(out_cost_amount), 0) as out_cost_amount
from product_detail_account WHERE id in %s group by product_id) middle_line on middle_line.product_id=start_line.product_id
LEFT JOIN (select balance_qty, balance_price, balance_amount, product_id
from product_detail_account where id in (select max(id) from product_detail_account WHERE id in %s group by product_id)) end_line
  ON end_line.product_id=start_line.product_id;""" % (record_string, record_string, record_string))
        balance_infos = self.env.cr.dictfetchall()
        for r in balance_infos:
            r['uom_id'] = [self.env['product.product'].browse(r['product_id']).product_tmpl_id.uom_id.id,
                           self.env['product.product'].browse(r['product_id']).product_tmpl_id.uom_id.name]
            r['product_id'] = [self.env['product.product'].browse(r['product_id']).id,
                               self.env['product.product'].browse(r['product_id']).name]
        # reorder read
        index = dict((r['id'], r) for r in balance_infos)
        res = [index[x] for x in index if x in index]
        return res

