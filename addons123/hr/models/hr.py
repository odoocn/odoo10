# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import time
from odoo import api, fields, models
from odoo import tools, _
from odoo.exceptions import ValidationError
from odoo.modules.module import get_module_resource

_logger = logging.getLogger(__name__)


class EmployeeCategory(models.Model):
    _name = "hr.employee.category"
    _description = "Employee Category"

    name = fields.Char(string="Employee Tag", required=True)
    color = fields.Integer(string='Color Index')
    employee_ids = fields.Many2many('hr.employee', 'employee_category_rel', 'category_id', 'emp_id', string='Employees')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]


class Job(models.Model):
    _name = "hr.job"
    _description = "Job Position"
    _inherit = ['mail.thread']

    name = fields.Char(string='Job Title', required=True, index=True, translate=True)
    expected_employees = fields.Integer(compute='_compute_employees', string='Total Forecasted Employees', store=True,
                                        help='Expected number of employees for this job position after new recruitment.')
    no_of_employee = fields.Integer(compute='_compute_employees', string="Current Number of Employees", store=True,
                                    help='Number of employees currently occupying this job position.')
    no_of_recruitment = fields.Integer(string='Expected New Employees', copy=False,
                                       help='Number of new employees you expect to recruit.', default=1)
    no_of_hired_employee = fields.Integer(string='Hired Employees', copy=False,
                                          help='Number of hired employees for this job position during recruitment phase.')
    employee_ids = fields.One2many('hr.employee', 'job_id', string='Employees', groups='base.group_user')
    description = fields.Text(string='Job Description')
    requirements = fields.Text('Requirements')
    department_id = fields.Many2one('hr.department', string='Department')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    state = fields.Selection([
        ('recruit', 'Recruitment in Progress'),
        ('open', 'Not Recruiting')
    ], string='Status', readonly=True, required=True, track_visibility='always', copy=False, default='recruit',
        help="Set whether the recruitment process is open or closed for this job position.")

    _sql_constraints = [
        ('name_company_uniq', 'unique(name, company_id, department_id)',
         'The name of the job position must be unique per department in company!'),
    ]

    @api.depends('no_of_recruitment', 'employee_ids.job_id', 'employee_ids.active')
    def _compute_employees(self):
        employee_data = self.env['hr.employee'].read_group([('job_id', 'in', self.ids)], ['job_id'], ['job_id'])
        result = dict((data['job_id'][0], data['job_id_count']) for data in employee_data)
        for job in self:
            job.no_of_employee = result.get(job.id, 0)
            job.expected_employees = result.get(job.id, 0) + job.no_of_recruitment

    @api.model
    def create(self, values):
        """ We don't want the current user to be follower of all created job """
        return super(Job, self.with_context(mail_create_nosubscribe=True)).create(values)

    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        if 'name' not in default:
            default['name'] = _("%s (copy)") % (self.name)
        return super(Job, self).copy(default=default)

    @api.multi
    def set_recruit(self):
        for record in self:
            no_of_recruitment = 1 if record.no_of_recruitment == 0 else record.no_of_recruitment
            record.write({'state': 'recruit', 'no_of_recruitment': no_of_recruitment})
        return True

    @api.multi
    def set_open(self):
        return self.write({
            'state': 'open',
            'no_of_recruitment': 0,
            'no_of_hired_employee': 0
        })


class Employee(models.Model):
    _name = "hr.employee"
    _description = "Employee"
    _order = 'name_related'
    _inherits = {'resource.resource': "resource_id"}
    _inherit = ['mail.thread']

    _mail_post_access = 'read'

    @api.model
    def _default_image(self):
        image_path = get_module_resource('hr', 'static/src/img', 'default_image.png')
        return tools.image_resize_image_big(open(image_path, 'rb').read().encode('base64'))

    # we need a related field in order to be able to sort the employee by name
    name_related = fields.Char(related='resource_id.name', string="Resource Name", readonly=True, store=True)
    country_id = fields.Many2one('res.country', string='Nationality (Country)')
    birthday = fields.Date('Date of Birth')
    ssnid = fields.Char('SSN No', help='Social Security Number')
    sinid = fields.Char('SIN No', help='Social Insurance Number')
    identification_id = fields.Char(string='Identification No')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ])
    marital = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('widower', 'Widower'),
        ('divorced', 'Divorced')
    ], string='Marital Status')
    department_id = fields.Many2one('hr.department', string='Department')
    address_id = fields.Many2one('res.partner', string='Working Address')
    address_home_id = fields.Many2one('res.partner', string='Home Address')
    bank_account_id = fields.Many2one('res.partner.bank', string='Bank Account Number',
                                      domain="[('partner_id', '=', address_home_id)]",
                                      help='Employee bank salary account')
    work_phone = fields.Char('Work Phone')
    mobile_phone = fields.Char('Work Mobile')
    work_email = fields.Char('Work Email')
    work_location = fields.Char('Work Location')
    notes = fields.Text('Notes')
    parent_id = fields.Many2one('hr.employee', string='Manager')
    category_ids = fields.Many2many('hr.employee.category', 'employee_category_rel', 'emp_id', 'category_id',
                                    string='Tags')
    child_ids = fields.One2many('hr.employee', 'parent_id', string='Subordinates')
    resource_id = fields.Many2one('resource.resource', string='Resource',
                                  ondelete='cascade', required=True, auto_join=True)
    coach_id = fields.Many2one('hr.employee', string='Coach')
    job_id = fields.Many2one('hr.job', string='Job Title')
    passport_id = fields.Char('Passport No')
    color = fields.Integer('Color Index', default=0)
    city = fields.Char(related='address_id.city')
    login = fields.Char(related='user_id.login', readonly=True)
    last_login = fields.Datetime(related='user_id.login_date', string='Latest Connection', readonly=True)
    # add by liyx
    registration_id = fields.Char(u'推送用户id')
    # 新增字段---孟令平
    education_id = fields.One2many('hr.education', 'employee_id', u'教育信息')
    work_id = fields.One2many('hr.work', 'employee_id', u'工作信息')
    family_id = fields.One2many('hr.family', 'employee_id', u'家庭成员信息')
    file_finished = fields.Boolean(u'关键档案提交完毕', default=False)
    file_list = fields.One2many('hr.file.line', 'employee_id', u'文件列表')
    nation = fields.Char('民族')
    hk_address = fields.Char('户口所在地', required=True)
    address = fields.Char('现居住地址', required=True)
    contact_person = fields.Char('紧急联系人', required=True)
    contact = fields.Char('紧急联系人电话', required=True)
    shbx = fields.Many2one('hr.shbx', u'社会保险缴纳形式')
    add_time = fields.Date('增员时间')
    minus_time = fields.Date('减员时间')
    gjj = fields.Many2one('hr.shbx', u'公积金缴纳形式')
    add_time2 = fields.Date('增员时间')
    minus_time2 = fields.Date('减员时间')
    work_card = fields.Char(u'工作居住证号')
    add_time3 = fields.Date(u'生效日期')
    minus_time3 = fields.Date(u'失效日期')
    salary = fields.Float('员工酬薪')
    political_status = fields.Selection([('public', '群众'), ('member', '团员'), ('party', '党员')], '政治面貌')
    in_date = fields.Date('入职日期')
    out_date = fields.Date('离职日期')
    years = fields.Char(string=u'工作年限')
    level = fields.Many2one('hr.level', u'行政级别')
    hr_history = fields.One2many('hr.history', 'employee_id', u'变更记录', domain=[('is_confirm', '=', True)])
    p_state = fields.Selection([('inposition', '在职'), ('out', '离职')], '在职状态', default='inposition')
    employ_type = fields.Selection([('1', '正式'), ('2', '兼职'), ('3', '实习生')], '员工类型')
    # ------------------------------------------------------------------------
    # image: all image fields are base64 encoded and PIL-supported
    image = fields.Binary("Photo", default=_default_image, attachment=True,
                          help="This field holds the image used as photo for the employee, limited to 1024x1024px.")
    image_medium = fields.Binary("Medium-sized photo", attachment=True,
                                 help="Medium-sized photo of the employee. It is automatically "
                                      "resized as a 128x128px image, with aspect ratio preserved. "
                                      "Use this field in form views or some kanban views.")
    image_small = fields.Binary("Small-sized photo", attachment=True,
                                help="Small-sized photo of the employee. It is automatically "
                                     "resized as a 64x64px image, with aspect ratio preserved. "
                                     "Use this field anywhere a small image is required.")

    @api.constrains('parent_id')
    def _check_parent_id(self):
        for employee in self:
            if not employee._check_recursion():
                raise ValidationError(_('Error! You cannot create recursive hierarchy of Employee(s).'))

    @api.onchange('address_id')
    def _onchange_address(self):
        self.work_phone = self.address_id.phone
        self.mobile_phone = self.address_id.mobile

    @api.onchange('company_id')
    def _onchange_company(self):
        address = self.company_id.partner_id.address_get(['default'])
        self.address_id = address['default'] if address else False

    @api.onchange('department_id')
    def _onchange_department(self):
        self.parent_id = self.department_id.manager_id

    @api.onchange('user_id')
    def _onchange_user(self):
        self.work_email = self.user_id.email
        self.name = self.user_id.name
        self.image = self.user_id.image

    # 修改----mlp===========================================
    @api.onchange('user_id')
    def change_partner(self):
        self.address_home_id = self.user_id.partner_id

    @api.model
    def create(self, vals):
        tools.image_resize_images(vals)
        if vals.get('department_id'):
            origin_dep_q = '入职'
            origin_dep_h = vals['department_id']
        else:
            origin_dep_q = '入职'
            origin_dep_h = ''
        if vals.get('job_id'):
            origin_pos_q = '入职'
            origin_pos_h = vals['job_id']
        else:
            origin_pos_q = '入职'
            origin_pos_h = ''
        newh = self.env['hr.history'].create({
            'employee_id': self.id,
            'origin_dep_q': origin_dep_q,
            'origin_dep_h': origin_dep_h,
            'origin_pos_q': origin_pos_q,
            'origin_pos_h': origin_pos_h,
            'change_date': time.strftime("%Y-%m-%d", time.localtime(time.time())),
            'is_confirm': True,
            'state': 'confirm'
        })
        vals['hr_history'] = newh
        employee_id = super(Employee, self).create(vals)
        newh.update({'employee_id': employee_id})
        return employee_id

    # ---------------------------------------------------------------
    @api.multi
    def write(self, vals):
        tools.image_resize_images(vals)
        return super(Employee, self).write(vals)

    @api.multi
    def unlink(self):
        resources = self.mapped('resource_id')
        super(Employee, self).unlink()
        return resources.unlink()

    # def onchange_department_id(self, cr, uid, ids, department_id, context=None):
    #     value = {'parent_id': False}
    #     if department_id:
    #         department = self.pool.get('hr.department').browse(cr, uid, department_id)
    #         value['parent_id'] = department.manager_id.id
    #     return {'value': value}

    @api.multi
    def action_follow(self):
        """ Wrapper because message_subscribe_users take a user_ids=None
            that receive the context without the wrapper.
        """
        return self.message_subscribe_users()

    @api.multi
    def action_unfollow(self):
        """ Wrapper because message_unsubscribe_users take a user_ids=None
            that receive the context without the wrapper.
        """
        return self.message_unsubscribe_users()

    @api.model
    def _message_get_auto_subscribe_fields(self, updated_fields, auto_follow_fields=None):
        """ Overwrite of the original method to always follow user_id field,
            even when not track_visibility so that a user will follow it's employee
        """
        if auto_follow_fields is None:
            auto_follow_fields = ['user_id']
        user_field_lst = []
        for name, field in self._fields.items():
            if name in auto_follow_fields and name in updated_fields and field.comodel_name == 'res.users':
                user_field_lst.append(name)
        return user_field_lst


class Department(models.Model):
    _name = "hr.department"
    _description = "Hr Department"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = "name"

    name = fields.Char('Department Name', required=True)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', index=True,
                                 default=lambda self: self.env.user.company_id)
    parent_id = fields.Many2one('hr.department', string='Parent Department', index=True)
    child_ids = fields.One2many('hr.department', 'parent_id', string='Child Departments')
    manager_id = fields.Many2one('hr.employee', string='Manager', track_visibility='onchange')
    member_ids = fields.One2many('hr.employee', 'department_id', string='Members', readonly=True)
    jobs_ids = fields.One2many('hr.job', 'department_id', string='Jobs')
    note = fields.Text('Note')
    color = fields.Integer('Color Index')

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('Error! You cannot create recursive departments.'))

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record.name
            if record.parent_id:
                name = "%s / %s" % (record.parent_id.name_get()[0][1], name)
            result.append((record.id, name))
        return result

    @api.model
    def create(self, vals):
        # TDE note: auto-subscription of manager done by hand, because currently
        # the tracking allows to track+subscribe fields linked to a res.user record
        # An update of the limited behavior should come, but not currently done.
        department = super(Department, self.with_context(mail_create_nosubscribe=True)).create(vals)
        manager = self.env['hr.employee'].browse(vals.get("manager_id"))
        if manager.user_id:
            department.message_subscribe_users(user_ids=manager.user_id.ids)
        return department

    @api.multi
    def write(self, vals):
        """ If updating manager of a department, we need to update all the employees
            of department hierarchy, and subscribe the new manager.
        """
        # TDE note: auto-subscription of manager done by hand, because currently
        # the tracking allows to track+subscribe fields linked to a res.user record
        # An update of the limited behavior should come, but not currently done.
        if 'manager_id' in vals:
            manager_id = vals.get("manager_id")
            if manager_id:
                manager = self.env['hr.employee'].browse(manager_id)
                # subscribe the manager user
                if manager.user_id:
                    self.message_subscribe_users(user_ids=manager.user_id.ids)
            employees = self.env['hr.employee']
            for department in self:
                employees = employees | self.env['hr.employee'].search([
                    ('id', '!=', manager_id),
                    ('department_id', '=', department.id),
                    ('parent_id', '=', department.manager_id.id)
                ])
            employees.write({'parent_id': manager_id})
        return super(Department, self).write(vals)


# 新增-----------------孟令平
class hr_chreasion(models.Model):
    _name = 'hr.chreasion'

    name = fields.Text(u'原因')
    style = fields.Selection([('up', '升职'), ('down', '降职'), ('change', '调岗'), ('go', '离职')], '类型')


class hr_history(models.Model):
    _name = "hr.history"
    _rec_name = 'employee_id'
    _order = 'change_date desc'

    @api.multi
    def draft(self):
        self.write({'state': 'draft'})

    @api.multi
    def confirm(self):
        id = self.employee_id.id
        self.write({'state': 'confirm'})
        obj = self.env['hr.employee'].search([('id', '=', self.employee_id.id)])
        obj.department_id = self.origin_dep_h
        obj.job_id = self.origin_pos_h
        objs = self.search([('employee_id', '=', id), ('id', '!=', self.id)])
        for op in objs:
            op.update({'is_now': '2'})
        products = self.search([('employee_id', '=', id), ('end_data', '=', False), ('id', '!=', self.id)])
        for product in products:
            product.end_data = self.change_date
        self.is_confirm = True

    employee_id = fields.Many2one('hr.employee', u'员工')
    change_date = fields.Date(u'变更时间')
    end_data = fields.Date(u'结束时间')
    origin_dep_q = fields.Char(u'变更前部门')
    origin_pos_q = fields.Char(u'变更前职位')
    origin_dep_h = fields.Many2one('hr.department', u'变更后部门')
    origin_pos_h = fields.Many2one('hr.job', u'变更后职位')
    change_reasion = fields.Many2one('hr.chreasion', u'变更原因')
    status = fields.Selection([('up', '升职'), ('down', '降职'), ('change', '调岗')], required=True, default='up',
                              string='类型')
    note = fields.Text(u'备注')
    state = fields.Selection([
        ('draft', '草稿'),
        ('confirm', '确认'),
    ],
        string='State',
        required=True,
        default='draft')
    is_now = fields.Selection([('1', '是'), ('2', '否')], u'是否当前', default='1')
    is_confirm = fields.Boolean(u'是否审核', default=False)

    @api.onchange('employee_id')
    def on_change(self):
        dep = self.employee_id.department_id.name
        pos = self.employee_id.job_id.name
        self.origin_dep_q = dep
        self.origin_pos_q = pos

    @api.model
    def create(self, vals):
        if vals['employee_id']:
            id = vals['employee_id']
            dep = self.env['hr.employee'].search([('id', '=', id)]).department_id.name
            pos = self.env['hr.employee'].search([('id', '=', id)]).job_id.name
            vals.update(origin_dep_q=dep, origin_pos_q=pos)
        return super(hr_history, self).create(vals)


class hr_goaway(models.Model):
    _name = 'hr.goaway'
    _rec_name ='employee_id'
    _order = 'change_date desc'

    @api.multi
    def confirm(self):
        id = self.employee_id.id
        self.write({'state': 'confirm'})
        obj = self.env['hr.employee'].search([('id', '=', self.employee_id.id)])
        obj.p_state = 'out'
        objs = self.env['hr.history'].search([('employee_id', '=', id)])
        for op in objs:
            op.update({'is_now': '2'})
        products = self.env['hr.history'].search([('employee_id', '=', id), ('end_data', '=', False)])
        for product in products:
            product.end_data = self.change_date
        self.is_confirm = True

    employee_id = fields.Many2one('hr.employee', u'员工')
    change_date = fields.Date(u'离职时间')
    origin_dep_q = fields.Char(u'部门')
    origin_pos_q = fields.Char(u'职位')
    change_reasion = fields.Many2one('hr.chreasion', u'离职原因')
    note = fields.Text(u'备注')
    state = fields.Selection([
        ('draft', '草稿'),
        ('confirm', '确认'),
    ],
        string='State',
        required=True,
        default='draft')
    is_confirm = fields.Boolean(u'是否审核', default=False)

    @api.onchange('employee_id')
    def on_change(self):
        dep = self.employee_id.department_id.name
        pos = self.employee_id.job_id.name
        self.origin_dep_q = dep
        self.origin_pos_q = pos

    @api.model
    def create(self, vals):
        hr_expense = super(hr_goaway, self).create(vals)
        if vals.get('employee_id'):
            hr_expense.origin_dep_q = hr_expense.employee_id.department_id.name
            hr_expense.origin_pos_q = hr_expense.employee_id.job_id.name
        return hr_expense

    @api.multi
    def write(self, vals):
        res = super(hr_goaway, self).write(vals)
        if vals.get('employee_id'):
            self.origin_dep_q = self.employee_id.department_id.name
            self.origin_pos_q = self.employee_id.job_id.name
        return res


class hr_level(models.Model):
    _name = "hr.level"

    name = fields.Char(string=u'名称', required=True)
    code = fields.Char(string=u'编码', required=True)
    description = fields.Char(string=u'说明')


class hr_shbx(models.Model):
    _name = "hr.shbx"

    name = fields.Char(string=u'社会保险缴纳形式', required=True)


class hr_file(models.Model):
    _name = "hr.file.line"
    # _rec_name = "name"

    name = fields.Selection([('photo', '照片'), ('eduction', '学历证书'), ('identify', '身份证复印件')], string='附件类型')
    ex_datas = fields.Binary(u'附件')
    ex_datas_fname = fields.Char(u'文件名')
    employee_id = fields.Many2one('hr.employee', u'员工')
    note = fields.Text(u'备注')


class hr_family(models.Model):
    _name = "hr.family"
    # _rec_name = "name"

    name = fields.Char(u'姓名', size=64, required=True)
    relationship = fields.Char(u'关系', size=64, required=True)
    work_unit = fields.Char(u'工作单位', size=128, required=True)
    post = fields.Char(u'岗位', size=64, required=True)
    contact_info = fields.Char(u'联系方式', required=True)
    employee_id = fields.Many2one('hr.employee', u'员工')
    backup = fields.Text(u'备注')


class hr_work(models.Model):
    _name = "hr.work"
    _description = ""
    # _rec_name = "work"

    work = fields.Char(u'工作单位', size=128, required=True)
    post = fields.Char(u'工作岗位', size=64, required=True)
    witness = fields.Char(u'证明人', required=True)
    contact_info = fields.Char(u'联系方式', required=True)
    start_time = fields.Date(u'起始时间', required=True)
    finish_time = fields.Date(u'结束时间', required=True)
    describe = fields.Text(u'工作经历描述')
    employee_id = fields.Many2one('hr.employee', u'员工')
    backup = fields.Text(u'备注')


class hr_education(models.Model):
    _name = "hr.education"
    _description = ""
    # _rec_name = "school"

    school = fields.Char(u'学校', size=128, required=True)
    professional = fields.Char(u'所学专业', size=64, required=True)
    diploma = fields.Many2one('hr.diploma', u'学历', required=True)
    start_time = fields.Date(u'起始时间', required=True)
    finish_time = fields.Date(u'结束时间', required=True)
    employee_id = fields.Many2one('hr.employee', u'员工')
    backup = fields.Text(u'备注')


class hr_diploma(models.Model):
    _name = "hr.diploma"

    name = fields.Char(string=u'名称', required=True)

    # -----------------------------------------------------------------------------------
