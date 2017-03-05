# -*- coding: utf-8 -*-

from datetime import date, datetime, timedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons import decimal_precision as dp


class MaintenanceStage(models.Model):
    """ Model for case stages. This models the main stages of a Maintenance Request management flow. """

    _name = 'maintenance.stage'
    _description = 'Maintenance Stage'
    _order = 'sequence, id'

    name = fields.Char('Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=20)
    fold = fields.Boolean('Folded in Maintenance Pipe')
    done = fields.Boolean('Request Done')


class MaintenanceEquipmentCategory(models.Model):
    _name = 'maintenance.equipment.category'
    _inherit = ['mail.alias.mixin', 'mail.thread']
    _description = 'Asset Category'

    @api.one
    @api.depends('equipment_ids')
    def _compute_fold(self):
        self.fold = False if self.equipment_count else True

    name = fields.Char('Category Name', required=True, translate=True)
    technician_user_id = fields.Many2one('res.users', 'Responsible', track_visibility='onchange', default=lambda self: self.env.uid, oldname='user_id')
    color = fields.Integer('Color Index')
    note = fields.Text('Comments', translate=True)
    equipment_ids = fields.One2many('maintenance.equipment', 'category_id', string='Equipments', copy=False)
    equipment_count = fields.Integer(string="Equipment", compute='_compute_equipment_count')
    maintenance_ids = fields.One2many('maintenance.request', 'category_id', copy=False)
    maintenance_count = fields.Integer(string="Maintenance", compute='_compute_maintenance_count')
    alias_id = fields.Many2one(
        'mail.alias', 'Alias', ondelete='cascade', required=True,
        help="Email alias for this equipment category. New emails will automatically "
        "create new maintenance request for this equipment category.")
    fold = fields.Boolean(string='Folded in Maintenance Pipe', compute='_compute_fold', store=True)

    @api.multi
    def _compute_equipment_count(self):
        equipment_data = self.env['maintenance.equipment'].read_group([('category_id', 'in', self.ids)], ['category_id'], ['category_id'])
        mapped_data = dict([(m['category_id'][0], m['category_id_count']) for m in equipment_data])
        for category in self:
            category.equipment_count = mapped_data.get(category.id, 0)

    @api.multi
    def _compute_maintenance_count(self):
        maintenance_data = self.env['maintenance.request'].read_group([('category_id', 'in', self.ids)], ['category_id'], ['category_id'])
        mapped_data = dict([(m['category_id'][0], m['category_id_count']) for m in maintenance_data])
        for category in self:
            category.maintenance_count = mapped_data.get(category.id, 0)

    @api.model
    def create(self, vals):
        self = self.with_context(alias_model_name='maintenance.request', alias_parent_model_name=self._name)
        if not vals.get('alias_name'):
            vals['alias_name'] = vals.get('name')
        category_id = super(MaintenanceEquipmentCategory, self).create(vals)
        category_id.alias_id.write({'alias_parent_thread_id': category_id.id, 'alias_defaults': {'category_id': category_id.id}})
        return category_id

    @api.multi
    def unlink(self):
        MailAlias = self.env['mail.alias']
        for category in self:
            if category.equipment_ids or category.maintenance_ids:
                raise UserError(_("You cannot delete an equipment category containing equipments or maintenance requests."))
            MailAlias += category.alias_id
        res = super(MaintenanceEquipmentCategory, self).unlink()
        MailAlias.unlink()
        return res

    def get_alias_model_name(self, vals):
        return vals.get('alias_model', 'maintenance.equipment')

    def get_alias_values(self):
        values = super(MaintenanceEquipmentCategory, self).get_alias_values()
        values['alias_defaults'] = {'category_id': self.id}
        return values

#********by mlp**************************
class Equipment_maintain(models.Model):
    _name='equipment.maintain'
    name=fields.Char(u'保养类型')


class Repair(models.Model):
    _inherit = 'mrp.repair'
    maintenance_id=fields.Many2one('maintenance.equipment',string='设备')

class Maintain_line(models.Model):
    _name='maintain.line'

    name = fields.Char('说明',required=True)
    equipment_id = fields.Many2one(
        'maintain.detail',
        index=True, ondelete='cascade')
    type = fields.Selection([
        ('add', '添加'),
        ('remove', '移除')], '类型', required=True)
    to_invoice = fields.Boolean('代开票')
    product_id = fields.Many2one('product.product', '产品', required=True)
    price_unit = fields.Float('单价', digits=dp.get_precision('Product Price'))
    tax_id = fields.Many2many('account.tax',string='税金')
    location_id = fields.Many2one(
        'stock.location', 'Source Location',
        index=True, required=True)
    location_dest_id = fields.Many2one(
        'stock.location', 'Dest. Location',
        index=True,)
    product_uom_qty = fields.Float(
        '数量', default=1.0,
        digits=dp.get_precision('Product Unit of Measure'), required=True)
    product_uom = fields.Many2one(
        'product.uom', 'Product Unit of Measure',
        )
    price_subtotal = fields.Float(u'小计', compute='_compute_price_subtotal', digits=0)
    request_id=fields.Many2one('maintenance.request')
    move_id=fields.Many2one('stock.move')
    state=fields.Selection([('1','未完成'),('done','完成')],default='1')


    @api.one
    @api.depends('to_invoice', 'price_unit', 'equipment_id', 'product_uom_qty', 'product_id')
    def _compute_price_subtotal(self):
        if not self.to_invoice:
            self.price_subtotal = 0.0
        else:
            taxes = self.env['account.tax'].compute_all(self.price_unit, self.equipment_id.pricelist_id.currency_id, self.product_uom_qty, self.product_id, self.equipment_id.partner_id)
            self.price_subtotal = taxes['total_excluded']


    @api.onchange('type')
    def onchange_operation_type(self):
        """ On change of operation type it sets source location, destination location
        and to invoice field.
        @param product: Changed operation type.
        @param guarantee_limit: Guarantee limit of current record.
        @return: Dictionary of values.
        """
        if not self.type:
            self.location_id = False
            self.Location_dest_id = False
        elif self.type == 'add':
            args=[]
            warehouse = self.env['stock.warehouse'].search(args, limit=1)
            self.location_id = warehouse.lot_stock_id
            self.location_dest_id = self.env['stock.location'].search([('usage', '=', 'production')], limit=1).id
            self.to_invoice =False
        else:
            self.location_id = self.env['stock.location'].search([('usage', '=', 'production')], limit=1).id
            self.location_dest_id = self.env['stock.location'].search([('scrap_location', '=', True)], limit=1).id
            self.to_invoice = False


    @api.onchange('product_id')
    def change_product_uom(self):
        self.product_uom = self.product_id.uom_id.id

class Maintain_detail(models.Model):
    _name='maintain.detail'
    _rec_name='equipment_id'

    maintain_introduce=fields.Char(u'保养描述',required=True)
    maintain_text=fields.Text(u'保养内容')
    maintain_type=fields.Many2one('equipment.maintain',string='保养类型')
    maintain_lines=fields.One2many('maintain.line','equipment_id',string='所需部件')
    equipment_id=fields.Many2one('maintenance.equipment')
    period = fields.Integer('Days between each preventive maintenance')
    next_action_date = fields.Date(compute='_compute_next_maintenance', string='Date of the next preventive maintenance', store=True)
    maintenance_duration = fields.Float(help="Maintenance Duration in minutes and seconds.")
    maintenance_ids = fields.One2many('maintenance.request', 'maintain_datail_id')

    pricelist_id = fields.Many2one(
        'product.pricelist', 'Pricelist',
        default=lambda self: self.env['product.pricelist'].search([], limit=1).id,
        help='Pricelist of the selected partner.')
    partner_id = fields.Many2one(
        'res.partner', 'Partner',
        index=True, states={'confirmed': [('readonly', True)]},
        help='Choose partner for whom the order will be invoiced and delivered.')


    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if not self.partner_id:
            # self.address_id = False
            # self.partner_invoice_id = False
            self.pricelist_id = self.env['product.pricelist'].search([], limit=1).id
        else:
            # addresses = self.partner_id.address_get(['delivery', 'invoice', 'contact'])
            # self.address_id = addresses['delivery'] or addresses['contact']
            # self.partner_invoice_id = addresses['invoice']
            self.pricelist_id = self.partner_id.property_product_pricelist.id

    @api.depends('period', 'maintenance_ids.request_date')
    def _compute_next_maintenance(self):
        for equipment in self:
            create_date = datetime.now()
            if equipment.period:
                next_date = create_date
                if equipment.maintenance_ids:
                    maintenance = equipment.maintenance_ids.sorted(lambda x: x.request_date)[0]
                    next_date = maintenance.request_date and datetime.strptime(maintenance.request_date, DEFAULT_SERVER_DATE_FORMAT) or create_date
                equipment.next_action_date = next_date and (next_date + timedelta(days=equipment.period)).strftime(DEFAULT_SERVER_DATE_FORMAT)



#*******************
class MaintenanceEquipment(models.Model):
    _name = 'maintenance.equipment'
    _inherit = ['mail.thread']
    _description = 'Equipment'

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'owner_user_id' in init_values and self.owner_user_id:
            return 'maintenance.mt_mat_assign'
        return super(MaintenanceEquipment, self)._track_subtype(init_values)

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            if record.name and record.serial_no:
                result.append((record.id, record.name + '/' + record.serial_no))
            if record.name and not record.serial_no:
                result.append((record.id, record.name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('name', '=', name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    name = fields.Char('Equipment Name', required=True, translate=True)
    active = fields.Boolean(default=True)
    technician_user_id = fields.Many2one('res.users', string='Technician', track_visibility='onchange', oldname='user_id')
    # owner_user_id = fields.Many2one('res.users', string='Owner', track_visibility='onchange') update by liyx 17/02/08
    owner_user_id = fields.Many2one('hr.department', string='Owner', track_visibility='onchange')  # add by liyx 17/02/08
    category_id = fields.Many2one('maintenance.equipment.category', string='设备类别',
                                  track_visibility='onchange', group_expand='_read_group_category_ids')
    partner_id = fields.Many2one('res.partner', string='Vendor', domain="[('supplier', '=', 1)]")
    partner_ref = fields.Char('Vendor Reference')
    location = fields.Char('Location')
    model = fields.Char('Model')
    serial_no = fields.Char('Serial Number', copy=False)
    assign_date = fields.Date('Assigned Date', track_visibility='onchange')
    cost = fields.Float('Cost')
    note = fields.Text('Note')
    warranty = fields.Date('Warranty')
    color = fields.Integer('Color Index')
    scrap_date = fields.Date('Scrap Date')
    maintenance_ids = fields.One2many('maintenance.request', 'equipment_id')
    maintenance_count = fields.Integer(compute='_compute_maintenance_count', string="Maintenance", store=True)
    maintenance_open_count = fields.Integer(compute='_compute_maintenance_count', string="Current Maintenance", store=True)
    period = fields.Integer('Days between each preventive maintenance')
    next_action_date = fields.Date(compute='_compute_next_maintenance', string='Date of the next preventive maintenance', store=True)
    maintenance_team_id = fields.Many2one('maintenance.team', string='Maintenance Team',required=True)
    maintenance_duration = fields.Float(help="Maintenance Duration in minutes and seconds.")

    # add by liyx 17/02/08
    state = fields.Selection([("0", "正常使用"), ("1", "借用"), ("3", "封存"), ("4", "报废"), ("5", "维修")], string="状态", default="0")
    manufacturer = fields.Char("制造商")
    purchase_date = fields.Date("采购日期")
    # add by mlp *****************
    maintenance_borrow_count=fields.Integer(compute='_count_borrow',  store=True)
    maintenance_fault_count=fields.Integer(compute='_count_fault',  store=True)
    maintenance_transfer_count=fields.Integer(compute='_count_transfer',  store=True)
    borrow_maintenance_ids = fields.One2many('equipment.borrow', 'equipment')
    fault_maintenance_ids = fields.One2many('equipment.fault', 'equipment')
    transfer_maintenance_ids = fields.One2many('equipment.transfer', 'equipment')

    maintain_detail_id=fields.One2many('maintain.detail','equipment_id',string='保养单')

    @api.depends('period', 'maintenance_open_count', 'maintenance_ids.request_date')
    def _compute_next_maintenance(self):
        for equipment in self:
            create_date = equipment.create_date and datetime.strptime(equipment.create_date, DEFAULT_SERVER_DATETIME_FORMAT)
            if equipment.period:
                next_date = create_date
                if equipment.maintenance_ids:
                    maintenance = equipment.maintenance_ids.sorted(lambda x: x.request_date)[0]
                    next_date = maintenance.request_date and datetime.strptime(maintenance.request_date, DEFAULT_SERVER_DATE_FORMAT) or create_date
                equipment.next_action_date = next_date and (next_date + timedelta(days=equipment.period)).strftime(DEFAULT_SERVER_DATE_FORMAT)

    @api.one
    @api.depends('maintenance_ids.stage_id.done')
    def _compute_maintenance_count(self):
        self.maintenance_count = len(self.maintenance_ids)
        self.maintenance_open_count = len(self.maintenance_ids.filtered(lambda x: not x.stage_id.done))

    @api.onchange('category_id')
    def _onchange_category_id(self):
        self.technician_user_id = self.category_id.technician_user_id

    _sql_constraints = [
        ('serial_no', 'unique(serial_no)', "Another asset already exists with this serial number!"),
    ]

    @api.model
    def create(self, vals):
        equipment = super(MaintenanceEquipment, self).create(vals)
        if equipment.owner_user_id:
            equipment.message_subscribe_users(user_ids=[equipment.owner_user_id.id])
        return equipment

    @api.multi
    def write(self, vals):
        if vals.get('owner_user_id'):
            self.message_subscribe_users(user_ids=[vals['owner_user_id']])
        return super(MaintenanceEquipment, self).write(vals)

    @api.model
    def _read_group_category_ids(self, categories, domain, order):
        """ Read group customization in order to display all the categories in
            the kanban view, even if they are empty.
        """
        category_ids = categories._search([], order=order, access_rights_uid=SUPERUSER_ID)
        return categories.browse(category_ids)

    @api.model
    def _cron_generate_requests(self):
        for equipment in self.search([]):
            if equipment.period and equipment.next_action_date == date.today().strftime(DEFAULT_SERVER_DATE_FORMAT):
                self.env['maintenance.request'].create({
                    'name': _('Preventive Maintenance - %s' % equipment.next_action_date),
                    'request_date': equipment.next_action_date,
                    'category_id': equipment.category_id.id,
                    'equipment_id': equipment.id,
                    'maintenance_type': 'preventive',
                })

    def button_disable(self):
        self.update({"state": "3"})

    def button_enable(self):
        self.update({"state": "0"})

#================ by mlp ********************************
    @api.one
    @api.depends('borrow_maintenance_ids')
    def _count_borrow(self):
        self.maintenance_borrow_count= len(self.borrow_maintenance_ids)
    @api.one
    @api.depends('fault_maintenance_ids')
    def _count_fault(self):
        self.maintenance_fault_count= len(self.fault_maintenance_ids)
    @api.one
    @api.depends('transfer_maintenance_ids')
    def _count_transfer(self):
        self.maintenance_transfer_count= len(self.transfer_maintenance_ids)

    @api.multi
    def button_maintain_request(self):
        obj=self.env['maintenance.request']
        for maintain_detail in self.maintain_detail_id:
            objs=obj.create({
                'name':maintain_detail.maintain_introduce,
                'owner_user_id':self.owner_user_id.id,
                'equipment_id':self.id,
                'maintenance_type':maintain_detail.maintain_type.id,
                'maintain_context':maintain_detail.maintain_text,
                'maintenance_team_id':self.maintenance_team_id.id,
            })
            for line in maintain_detail.maintain_lines:
                line.request_id=objs.id


class MaintenanceRequest(models.Model):
    _name = 'maintenance.request'
    _inherit = ['mail.thread']
    _description = 'Maintenance Requests'
    _order = "id desc"

    @api.returns('self')
    def _default_stage(self):
        return self.env['maintenance.stage'].search([], limit=1)

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'stage_id' in init_values and self.stage_id.sequence <= 1:
            return 'maintenance.mt_req_created'
        elif 'stage_id' in init_values and self.stage_id.sequence > 1:
            return 'maintenance.mt_req_status'
        return super(MaintenanceRequest, self)._track_subtype(init_values)

    def _get_default_team_id(self):
        return self.env.ref('maintenance.equipment_team_maintenance', raise_if_not_found=False)

    name = fields.Char('Subjects', required=True)
    description = fields.Text('Description')
    request_date = fields.Date('Request Date', track_visibility='onchange', default=fields.Date.context_today)

    owner_user_id = fields.Many2one('res.users', string='Created by', default=lambda s: s.env.uid)
    category_id = fields.Many2one('maintenance.equipment.category', related='equipment_id.category_id', string='Category', store=True, readonly=True)
    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment', index=True)
    technician_user_id = fields.Many2one('res.users', string='Owner', track_visibility='onchange', oldname='user_id')
    stage_id = fields.Many2one('maintenance.stage', string='Stage', track_visibility='onchange',
                               group_expand='_read_group_stage_ids', default=_default_stage)
    priority = fields.Selection([('0', 'Very Low'), ('1', 'Low'), ('2', 'Normal'), ('3', 'High')], string='Priority')
    color = fields.Integer('Color Index')
    close_date = fields.Date('Close Date')
    kanban_state = fields.Selection([('normal', 'In Progress'), ('blocked', 'Blocked'), ('done', 'Ready for next stage')],
                                    string='Kanban State', required=True, default='normal', track_visibility='onchange')
    # active = fields.Boolean(default=True, help="Set active to false to hide the maintenance request without deleting it.")
    archive = fields.Boolean(default=False, help="Set archive to true to hide the maintenance request without deleting it.")
    # maintenance_type = fields.Selection([('corrective', 'Corrective'), ('preventive', 'Preventive')], string='Maintenance Type', default="corrective")
    maintenance_type=fields.Many2one('equipment.maintain','保养类型')
    schedule_date = fields.Datetime('Scheduled Date')
    maintenance_team_id = fields.Many2one('maintenance.team', string='Team', required=True, default=_get_default_team_id)
    duration = fields.Float(help="Duration in minutes and seconds.")
    # by mlp *******************
    maintain_datail_id=fields.Many2one('maintain.detail')
    maintain_context=fields.Text(u'保养内容')
    maintain_line=fields.One2many('maintain.line','request_id',string='部件明细')





    @api.multi
    def archive_equipment_request(self):
        return self.write({'archive': True})

    @api.multi
    def reset_equipment_request(self):
        """ Reinsert the maintenance request into the maintenance pipe in the first stage"""
        first_stage_obj = self.env['maintenance.stage'].search([], order="sequence asc", limit=1)
        # self.write({'active': True, 'stage_id': first_stage_obj.id})
        return self.write({'archive': False, 'stage_id': first_stage_obj.id})

    @api.onchange('equipment_id')
    def onchange_equipment_id(self):
        if self.equipment_id:
            self.technician_user_id = self.equipment_id.technician_user_id if self.equipment_id.technician_user_id else self.equipment_id.category_id.technician_user_id
            self.category_id = self.equipment_id.category_id
            if self.equipment_id.maintenance_team_id:
                self.maintenance_team_id = self.equipment_id.maintenance_team_id.id

    @api.onchange('category_id')
    def onchange_category_id(self):
        if not self.technician_user_id or not self.equipment_id or (self.technician_user_id and not self.equipment_id.technician_user_id):
            self.technician_user_id = self.category_id.technician_user_id

    @api.model
    def create(self, vals):
        # context: no_log, because subtype already handle this
        self = self.with_context(mail_create_nolog=True)
        request = super(MaintenanceRequest, self).create(vals)
        if request.owner_user_id:
            request.message_subscribe_users(user_ids=[request.owner_user_id.id])
        if request.equipment_id and not request.maintenance_team_id:
            request.maintenance_team_id = request.equipment_id.maintenance_team_id
        return request

    @api.multi
    def write(self, vals):
        # Overridden to reset the kanban_state to normal whenever
        # the stage (stage_id) of the Maintenance Request changes.
        if vals and 'kanban_state' not in vals and 'stage_id' in vals:
            vals['kanban_state'] = 'normal'
        if vals.get('owner_user_id'):
            self.message_subscribe_users(user_ids=[vals['owner_user_id']])
        res = super(MaintenanceRequest, self).write(vals)
        if self.stage_id.done and 'stage_id' in vals:
            self.write({'close_date': fields.Date.today()})
            #====by mlp ******************************
            Move = self.env['stock.move']
            for repair in self:
                moves = self.env['stock.move']
                for operation in repair.maintain_line:
                    move = Move.create({
                        'name': operation.name,
                        'product_id': operation.product_id.id,
                        # 'restrict_lot_id': operation.lot_id.id,
                        'product_uom_qty': operation.product_uom_qty,
                        'product_uom': operation.product_uom.id,
                        # 'partner_id': repair.address_id.id,
                        'location_id': operation.location_id.id,
                        'location_dest_id': operation.location_dest_id.id,
                        'state':'done',
                    })
                    moves |= move
                    if operation.type=='add':
                        moves.action_done()
                    operation.write({'move_id': move.id, 'state': 'done'})
        return res

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """ Read group customization in order to display all the stages in the
            kanban view, even if they are empty
        """
        stage_ids = stages._search([], order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)


class MaintenanceTeam(models.Model):
    _name = 'maintenance.team'
    _description = 'Maintenance Teams'

    name = fields.Char(required=True)
    partner_id = fields.Many2one('res.partner', string='Subcontracting Partner')
    color = fields.Integer(default=0)
    request_ids = fields.One2many('maintenance.request', 'maintenance_team_id', copy=False)
    equipment_ids = fields.One2many('maintenance.equipment', 'maintenance_team_id', copy=False)

    # For the dashboard only
    todo_request_ids = fields.One2many('maintenance.request', copy=False, compute='_compute_todo_requests')
    todo_request_count = fields.Integer(compute='_compute_todo_requests')
    todo_request_count_date = fields.Integer(compute='_compute_todo_requests')
    todo_request_count_high_priority = fields.Integer(compute='_compute_todo_requests')
    todo_request_count_block = fields.Integer(compute='_compute_todo_requests')

    @api.one
    @api.depends('request_ids.stage_id.done')
    def _compute_todo_requests(self):
        self.todo_request_ids = self.request_ids.filtered(lambda e: e.stage_id.done==False)
        self.todo_request_count = len(self.todo_request_ids)
        self.todo_request_count_date = len(self.todo_request_ids.filtered(lambda e: e.schedule_date != False))
        self.todo_request_count_high_priority = len(self.todo_request_ids.filtered(lambda e: e.priority == '3'))
        self.todo_request_count_block = len(self.todo_request_ids.filtered(lambda e: e.kanban_state == 'blocked'))

    @api.one
    @api.depends('equipment_ids')
    def _compute_equipment(self):
        self.equipment_count = len(self.equipment_ids)
