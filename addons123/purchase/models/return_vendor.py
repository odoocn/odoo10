# -*- coding: utf-8 -*-
# ===zhy

from odoo import api, fields, models, _
import logging


class ReturnVendor(models.Model):
    _name = "return.vendor"

    @api.model
    def _default_warehouse(self):
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_id)])
        return warehouse[:1]

    @api.model
    def _default_dest(self):
        location = self.env['stock.location'].search([('usage', '=', 'supplier')])
        if location:
            return location[0]
        else:
            return False

    READONLY_STATES = {
        'draft': [('readonly', False)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    name = fields.Char(string=u'退货单号', required=True, states=READONLY_STATES)
    vendor = fields.Many2one('res.partner', string=u'供应商', states=READONLY_STATES, required=True)
    purchase_id = fields.Many2one('purchase.order', string=u'采购订单', states=READONLY_STATES, required=True)
    line_ids = fields.One2many('return.vendor.line', 'return_id', string=u'明细', states=READONLY_STATES)
    picking = fields.Many2one('stock.picking', string=u'进货单', states=READONLY_STATES, required=True,
                              domain="[('state','=','done')]")
    state = fields.Selection([('draft', '草稿'), ('done', '完成'), ('cancel', '取消')], string=u'状态', default='draft')
    int_picking = fields.Many2one('stock.picking', string=u'调拨单', states=READONLY_STATES)

    warehouse = fields.Many2one('stock.warehouse', string=u'仓库', default=_default_warehouse, states=READONLY_STATES,
                                required=True)
    dest_loc = fields.Many2one('stock.location', string=u'目标位置', domain="[('usage','=','supplier')]",
                               default=_default_dest, states=READONLY_STATES, required=True)

    @api.multi
    def button_cancel(self):
        self.write({'state': 'cancel'})

    @api.onchange('purchase_id')
    def onchange_purchase_id(self):
        _logger = logging.getLogger(__name__)
        _logger.info('temp')
        self.picking = False
        self.line_ids = []

    @api.onchange('picking')
    def get_line(self):
        self.line_ids = []
        if self.picking:
            new_lines = self.env['return.vendor.line']
            for line in self.picking.move_lines:
                data = {
                    'return_id': self.id,
                    'product_id': line.product_id.id,
                    'product_qty': line.product_qty,
                    'return_qty': 0.0,
                    'purchase_line': line.purchase_line_id.id,
                }
                new_line = new_lines.new(data)

    @api.one
    def return_item(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        move_lines = []
        for line in self.line_ids:
            move_lines.append([0, 0, {'name': line.product_id.product_tmpl_id.name,
                                      'product_id': line.product_id.id,
                                      'product_uom_qty': line.return_qty,
                                      'product_uom': line.product_id.product_tmpl_id.uom_id.id,
                                      'purchase_line_id': line.purchase_line.id}])
        warehouse = self.warehouse
        picking = self.env['stock.picking'].create({'location_id': warehouse.wh_return_stock_loc_id.id,
                                                    'location_dest_id': self.dest_loc.id,
                                                    'origin': self.name,
                                                    'partner_id': self.vendor.id,
                                                    'picking_type_id': warehouse.rv_type_id.id,
                                                    'move_lines': move_lines})
        self.write({'int_picking': picking.id})
        picking.action_confirm()
        picking.force_assign()

        self.write({'state': 'done'})


class ReturnVendorLine(models.Model):
    _name = "return.vendor.line"

    return_id = fields.Many2one('return.vendor', string=u'单号', required=True)
    product_id = fields.Many2one('product.product', string=u'产品名称', required=True)
    product_qty = fields.Float(string=u'采购数量')
    return_qty = fields.Float(string=u'退货数量')
    description = fields.Text(string=u'备注')
    purchase_line = fields.Many2one('purchase.order.line')
    barcode = fields.Char(string=u'条码', related='product_id.barcode')

    _sql_constraints = [
        ('vendor_return_line_qty_check', 'check(product_qty >= return_qty)',
         u'退货数量不能大于原采购数量！')
    ]
