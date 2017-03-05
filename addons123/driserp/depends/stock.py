# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api, _, models, fields
from odoo.tools.float_utils import float_compare, float_round
from odoo.exceptions import UserError
from cStringIO import StringIO
import xlwt
from datetime import datetime
from datetime import timedelta


class MStockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = 'stock.picking'

    sale_id = fields.Many2one(comodel_name='sale.order', string=u"销售订单",
                              compute='_compute_sale_id', search='_search_sale_id', store=True)


class DStockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = 'stock.picking'

    _order = 'destination_mark'

    express_code = fields.Char(compute='compute_express', store=True, string=u'快递单号')
    check_person = fields.Many2one('res.users', string=u'负责人')
    direct_group = fields.Selection([('2B', 'To B'), ('2C', 'To C')], string=u'面向对象', compute='compute_express')
    printed = fields.Boolean(default=False, string=u'已打印')
    destination_mark = fields.Char(string=u'大头笔', compute='compute_express', store=True)
    # ==Xuwentao
    plate_code = fields.Char(compute='compute_plate', string=u'平台订单号', store=True)
    source_shop = fields.Many2one('ecps.shop', string=u'来源店铺', compute='compute_plate', store=True)
    warehouse = fields.Char(string=u'仓库', compute='compute_plate', store=True)
    location_details = fields.Char(string=u'详细地址', compute='compute_plate')
    online_type = fields.Selection([('online', '线上'), ('offline', '线下')], string=u'订单来源', compute='compute_plate')
    order_start_time = fields.Datetime(string=u'下单时间', compute='compute_plate', store=True)

    # --Xuwentao

    def set_style(self, name, height, bold=False, center=True, borders=True):
        style = xlwt.XFStyle()  # 初始化样式
        font = xlwt.Font()  # 为样式创建字体
        if borders:
            borders = xlwt.Borders()
            borders.left = 1
            borders.right = 1
            borders.top = 1
            borders.bottom = 1
            borders.bottom_colour = 0x3A
            style.borders = borders
        al = xlwt.Alignment()
        if center:
            al.horz = xlwt.Alignment.HORZ_CENTER  # 设置水平居中
        al.vert = xlwt.Alignment.VERT_CENTER  # 设置垂直居中
        al.wrap = xlwt.Alignment.WRAP_AT_RIGHT  # 设置文字可以换行
        style.alignment = al
        font.name = name
        font.bold = bold
        font.color_index = 4
        font.height = height * 20
        style.font = font
        return style

    @api.multi
    def print_delivery_picking(self):
        self.ensure_one()
        workbook = xlwt.Workbook()
        sheet1 = workbook.add_sheet(u'sheet1', cell_overwrite_ok=True)
        sheet1.col(1).width = 16500
        sheet1.col(2).width = 2750
        sheet1.col(3).width = 2750
        tall_style = xlwt.easyxf('font:height 720;')  # 36pt,类型小初的字号
        first_row = sheet1.row(2)
        first_row.set_style(tall_style)
        sheet1.write_merge(0, 0, 0, 5, u"%s 发货清单" % self.sale_id.source_shop.name,
                           self.set_style(u'宋体', 16, True, True, False))
        sheet1.write_merge(1, 1, 0, 1, u"发往：%s  %s  %s" % (
            self.sale_id.source_shop.partner_id.name, self.sale_id.deliverCenterName, self.sale_id.warehouseName),
                           self.set_style(u'宋体', 14, True, False))
        sheet1.write_merge(1, 1, 2, 5, u"运单号:", self.set_style(u'宋体', 16, True, False))
        sheet1.write_merge(2, 2, 0, 5, u"地址:%s %s %s" % (
            self.sale_id.location_details, self.sale_id.delivery_name, self.sale_id.delivery_phone),
                           self.set_style(u'宋体', 14, True, False))
        sheet1.write(3, 0, u"采购单号:", self.set_style(u'宋体', 9, False))
        sheet1.write(3, 1, u"%s" % self.sale_id.source_code, self.set_style(u'宋体', 20, True))
        sheet1.write(3, 2, u"商家名称:", self.set_style(u'宋体', 9, False))
        sheet1.write_merge(3, 3, 3, 5, self.sale_id.source_shop.account_id.name, self.set_style(u'宋体', 9, False))
        sheet1.write(4, 0, u"采购员:", self.set_style(u'宋体', 9, False))
        sheet1.write(4, 1, u"%s" % self.sale_id.pur_erp, self.set_style(u'宋体', 9, True))
        sheet1.write(4, 2, u"订购日期:", self.set_style(u'宋体', 9, False))
        sheet1.write_merge(4, 4, 3, 5, (
            datetime.strptime(self.sale_id.order_start_time, "%Y-%m-%d %H:%M:%S") + timedelta(hours=8)).strftime(
            "%Y/%m/%d"), self.set_style(u'宋体', 9, False))
        sheet1.write(5, 0, u"商品编码", self.set_style(u'宋体', 9, False))
        sheet1.write(5, 1, u"商品名称", self.set_style(u'宋体', 10, True))
        sheet1.write(5, 2, u"采购数量(个)", self.set_style(u'宋体', 8, False))
        sheet1.write(5, 3, u"实发数量(个)", self.set_style(u'宋体', 8, False))
        sheet1.write(5, 4, u"箱子号码", self.set_style(u'宋体', 9, False))
        sheet1.write(5, 5, u"备注", self.set_style(u'宋体', 9, False))
        i = 0
        amount = 0
        for picking_line in self.move_lines:
            sheet1.write(6 + i, 0, picking_line.procurement_id.sale_line_id.item_id.item_sku,
                         self.set_style(u'宋体', 9, False))
            sheet1.write(6 + i, 1, picking_line.procurement_id.sale_line_id.item_id.name,
                         self.set_style(u'宋体', 9, False, False))
            sheet1.write(6 + i, 2, picking_line.procurement_id.sale_line_id.product_uom_qty,
                         self.set_style(u'宋体', 9, False))
            sheet1.write(6 + i, 3, "", self.set_style(u'宋体', 9, False))
            sheet1.write(6 + i, 4, "", self.set_style(u'宋体', 9, False))
            sheet1.write(6 + i, 5, "", self.set_style(u'宋体', 9, False))
            i += 1
            amount += picking_line.procurement_id.sale_line_id.product_uom_qty

        sheet1.write_merge(6 + i, 6 + i, 0, 1, u"采购订单数量总计", self.set_style(u'宋体', 12, True))
        sheet1.write(6 + i, 2, str(amount), self.set_style(u'宋体', 12, True))
        sheet1.write_merge(6 + i, 6 + i, 3, 4, u"实际发货数量", self.set_style(u'宋体', 12, True))
        sheet1.write(6 + i, 5, "", self.set_style(u'宋体', 12, True))
        i += 1

        sheet1.write_merge(6 + i, 6 + i, 0, 1, u"此单共 %s (种类)  商品" % str(i - 1), self.set_style(u'宋体', 12, True))
        sheet1.write(6 + i, 2, u"收货人：", self.set_style(u'宋体', 12, True))
        sheet1.write(6 + i, 3, self.sale_id.delivery_name, self.set_style(u'宋体', 12, True))
        sheet1.write(6 + i, 4, u"日期：", self.set_style(u'宋体', 12, True))
        sheet1.write(6 + i, 5, "", self.set_style(u'宋体', 12, True))
        i += 1

        sheet1.write_merge(6 + i, 6 + i, 0, 5, u"此单共        件", self.set_style(u'宋体', 24, True))
        i += 1

        sheet1.write_merge(6 + i, 6 + i, 0, 5, u"重要:", self.set_style(u'宋体', 11, True, False, False))
        i += 1

        sheet1.write_merge(6 + i, 6 + i, 0, 5, u"   如有任何疑问请立即联系：袁先生：18001029137       杨先生：18001170702 谢谢！",
                           self.set_style(u'宋体', 11, True, False, False))
        i += 1

        sheet1.write_merge(6 + i, 6 + i, 0, 5, u"   此单一联及收货方收货入库单需返回给东方万佳！否则不予结算运费，后果自负！",
                           self.set_style(u'宋体', 11, True, False, False))
        i += 1

        sheet1.write(6 + i, 0, u"制单人：", self.set_style(u'宋体', 8, False, True, False))
        sheet1.write(6 + i, 2, u"备货人：", self.set_style(u'宋体', 8, False, True, False))
        sheet1.write_merge(6 + i, 6 + i, 4, 5, u"", self.set_style(u'宋体', 8, False, True, False))
        sheet1.write(7 + i, 0, u"复核人：", self.set_style(u'宋体', 8, False, True, False))
        sheet1.write(7 + i, 2, u"发货日期：", self.set_style(u'宋体', 8, False, True, False))

        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        return data

    @api.multi
    def print_ready_picking(self):
        self.ensure_one()
        wave = self
        order = wave.sale_id
        source_code = order.source_code  # 订单号
        location_details = order.warehouseName  # 仓库地址
        start_picking_time = ''  # 开始备货时间
        bill_time = ''  # 交单时间
        picking_person = ''  # 备货人
        order_start_time = order.order_start_time  # 订单日期
        deliverCenterName = order.deliverCenterName  # 分配机构

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('wave' + str(wave.id))
        worksheet.col(0).width = 0x0d00 - 2000
        worksheet.col(1).width = 0x0d00 + 2000
        worksheet.col(3).width = 0x0d00 + 15000
        worksheet.write_merge(0, 3, 0, 7,
                              u"订单号： %s  开始备货时间:  %s  交单时间:  %s  备货人:  %s                 订单日期:  %s  分配机构:  %s  仓库地址:  %s" % (
                                  source_code, start_picking_time, bill_time, picking_person, (
                                      datetime.strptime(order_start_time, "%Y-%m-%d %H:%M:%S") + timedelta(
                                          hours=8)).strftime("%Y/%m/%d"),
                                  deliverCenterName, location_details),
                              self.set_style(u'宋体', 15, True))
        worksheet.write(4, 0, u'序号', self.set_style(u'宋体', 8, True))
        worksheet.write(4, 1, u'69码', self.set_style(u'宋体', 8, True))
        worksheet.write(4, 2, u'商品编码', self.set_style(u'宋体', 8, True))
        worksheet.write(4, 3, u'商品名称', self.set_style(u'宋体', 8, True))
        worksheet.write(4, 4, u'采购数量', self.set_style(u'宋体', 8, True))
        worksheet.write(4, 5, u'实发数量', self.set_style(u'宋体', 8, True))
        worksheet.write(4, 6, u'核算箱数', self.set_style(u'宋体', 8, True))
        worksheet.write(4, 7, u'编箱号码', self.set_style(u'宋体', 8, True))

        num = 1
        row = 5
        base_style = xlwt.easyxf('align: wrap yes')
        for line in self.move_lines:
            item = line.procurement_id.sale_line_id.item_id
            barcode = item.barcode  # 69码
            sku = item.item_sku  # 商品编码
            name = line.procurement_id.sale_line_id.product_id.product_tmpl_id.name  # 商品名称
            originalNum = line.procurement_id.sale_line_id.product_uom_qty  # 采购数量
            worksheet.write(row, 0, num, self.set_style(u'宋体', 8, False))
            worksheet.write(row, 1, barcode, self.set_style(u'宋体', 8, False))
            worksheet.write(row, 2, sku, self.set_style(u'宋体', 8, False))
            worksheet.write(row, 3, name, self.set_style(u'宋体', 8, False, False))
            worksheet.write(row, 4, originalNum, self.set_style(u'宋体', 8, False))
            worksheet.write(row, 5, "", self.set_style(u'宋体', 8, False))
            worksheet.write(row, 6, "", self.set_style(u'宋体', 8, False))
            worksheet.write(row, 7, "", self.set_style(u'宋体', 8, False))
            row += 1
            num += 1

        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        return data

    @api.depends('sale_id')
    def compute_express(self):
        for r in self:
            r.direct_group = r.sale_id.direct_group
            r.express_code = r.sale_id.express_code
            r.destination_mark = r.sale_id.location_mark

    @api.depends('sale_id')
    def compute_plate(self):
        for r in self:
            if r.sale_id.online_type == 'online':
                r.online_type = 'online'
                r.plate_code = r.sale_id.source_code
                r.source_shop = r.sale_id.source_shop.id
                r.warehouse = r.sale_id.warehouseName
                r.location_details = r.sale_id.location_details
                r.order_start_time = r.sale_id.order_start_time
                # xuwentao

    @api.multi
    def PDA_check(self, express_code):
        for picking in self.search([('express_code', '=', express_code)]):
            picking.write({'check_person': self.env.user.id})
            picking.do_transfer()

    @api.multi
    def do_new_transfer(self):
        for pick in self:
            if not pick.order_date:
                pick.order_date = fields.Date.today()
            pack_operations_delete = self.env['stock.pack.operation']
            if not pick.move_lines and not pick.pack_operation_ids:
                raise UserError(_('Please create some Initial Demand or Mark as Todo and create some Operations. '))
            # In draft or with no pack operations edited yet, ask if we can just do everything
            # 从捡货波次确认而来,则直接更改完成数
            if self.env.context.get('picking_done'):
                if pick.state == 'draft':
                    pick.action_confirm()
                    if pick.state != 'assigned':
                        pick.action_assign()
                        if pick.state != 'assigned':
                            raise UserError(_(
                                "Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
                for pack in pick.pack_operation_ids:
                    if pack.product_qty > 0:
                        pack.write({'qty_done': pack.product_qty})
                    else:
                        pack.unlink()
            elif pick.state == 'draft' or all([x.qty_done == 0.0 for x in pick.pack_operation_ids]):
                # If no lots when needed, raise error
                picking_type = pick.picking_type_id
                if (picking_type.use_create_lots or picking_type.use_existing_lots):
                    for pack in pick.pack_operation_ids:
                        if pack.product_id and pack.product_id.tracking != 'none':
                            raise UserError(
                                _('Some products require lots/serial numbers, so you need to specify those first!'))
                view = self.env.ref('stock.view_immediate_transfer')
                wiz = self.env['stock.immediate.transfer'].create({'pick_id': pick.id})
                # TDE FIXME: a return in a loop, what a good idea. Really.
                return {
                    'name': _('Immediate Transfer?'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'stock.immediate.transfer',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'res_id': wiz.id,
                    'context': self.env.context,
                }

            # Check backorder should check for other barcodes
            if pick.check_backorder():
                view = self.env.ref('stock.view_backorder_confirmation')
                wiz = self.env['stock.backorder.confirmation'].create({'pick_id': pick.id})
                # TDE FIXME: same reamrk as above actually
                return {
                    'name': _('Create Backorder?'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'stock.backorder.confirmation',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'res_id': wiz.id,
                    'context': self.env.context,
                }
            for operation in pick.pack_operation_ids:
                if operation.qty_done < 0:
                    raise UserError(_('No negative quantities allowed'))
                if operation.qty_done > 0:
                    operation.write({'product_qty': operation.qty_done})
                else:
                    pack_operations_delete |= operation
            if pack_operations_delete:
                pack_operations_delete.unlink()
        self.do_transfer()
        return

    @api.multi
    def do_transfer(self):
        """ If no pack operation, we do simple action_done of the picking.
        Otherwise, do the pack operations. """
        # TDE CLEAN ME: reclean me, please
        self._create_lots_for_picking()

        no_pack_op_pickings = self.filtered(lambda picking: not picking.pack_operation_ids)
        no_pack_op_pickings.action_done()
        other_pickings = self - no_pack_op_pickings
        for picking in other_pickings:
            if not picking.pack_operation_ids:
                self.action_done([picking.id])
                continue
            else:
                need_rereserve, all_op_processed = picking.picking_recompute_remaining_quantities()
                todo_moves = self.env['stock.move']
                toassign_moves = self.env['stock.move']

                # create extra moves in the picking (unexpected product moves coming from pack operations)
                if not all_op_processed:
                    todo_moves |= picking._create_extra_moves()

                if need_rereserve or not all_op_processed:
                    moves_reassign = any(x.origin_returned_move_id or x.move_orig_ids for x in picking.move_lines if
                                         x.state not in ['done', 'cancel'])
                    if moves_reassign and picking.location_id.usage not in ("supplier", "production", "inventory"):
                        # unnecessary to assign other quants than those involved with pack operations as they will be unreserved anyways.
                        picking.with_context(reserve_only_ops=True, no_state_change=True).rereserve_quants(
                            move_ids=todo_moves.ids)
                    picking.do_recompute_remaining_quantities()

                # split move lines if needed
                for move in picking.move_lines:
                    rounding = move.product_id.uom_id.rounding
                    remaining_qty = move.remaining_qty
                    if move.state in ('done', 'cancel'):
                        # ignore stock moves cancelled or already done
                        continue
                    elif move.state == 'draft':
                        toassign_moves |= move
                    if float_compare(remaining_qty, 0, precision_rounding=rounding) == 0:
                        if move.state in ('draft', 'assigned', 'confirmed'):
                            todo_moves |= move
                    elif float_compare(remaining_qty, 0, precision_rounding=rounding) > 0 and float_compare(
                            remaining_qty, move.product_qty, precision_rounding=rounding) < 0:
                        # TDE FIXME: shoudl probably return a move - check for no track key, by the way
                        new_move_id = move.split(remaining_qty)
                        new_move = self.env['stock.move'].with_context(mail_notrack=True).browse(new_move_id)
                        todo_moves |= move
                        # Assign move as it was assigned before
                        toassign_moves |= new_move

                # TDE FIXME: do_only_split does not seem used anymore
                if todo_moves and not self.env.context.get('do_only_split'):
                    todo_moves.action_done()
                elif self.env.context.get('do_only_split'):
                    picking = picking.with_context(split=todo_moves.ids)
            if picking.direct_group == '2C' and picking.picking_type_id.code == 'outgoing':
                pack = picking.put_in_pack()
                if picking.sale_id.express_code:
                    pack.write({'name': picking.sale_id.express_code})
            picking.write({'check_person': self.env.user.id})
            picking._create_backorder()
        return True


class EPurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = "purchase.order"

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    @api.model
    def _default_picking_type_e(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_id)])
        if warehouse:
            picking_type = warehouse[0].in_type_id
            if picking_type:
                return picking_type
        types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])
        if not types:
            types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
        return types[:1]

    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', states=READONLY_STATES, required=True,
                                      default=_default_picking_type_e,
                                      help="This will determine picking type of incoming shipment")
