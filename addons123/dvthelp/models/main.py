#coding:utf8
from odoo import fields, models


class HELP_FIRST(models.Model):
    _name = 'help.first'
    name = fields.Char(u'名称')
    type = fields.Selection([('Newproblems','最新问题'),('Classicalproblem','经典问题'),('Routineproblem','常规问题')],u'问题类型')
    name_id = fields.One2many('help.second','second_id',u'帮助文档')


class HELP_second(models.Model):
    _name = 'help.second'
    _order = 'num'
    name = fields.Char(u'名称')
    second_id = fields.Many2one('help.first', u'帮助主题')
    context = fields.Html(u'文档')
    num = fields.Integer(u'编号')


# class hr_chreasion(osv.osv):
#     _name='hr.chreasion'
#     _columns={
#         'name':fields.text(u'原因'),
#         'style':fields.selection([('up','升职'),('down','降职'),('change','调岗'),('go','离职')],'类型')
#     }
# class hr_history(osv.osv):
#     _name = "hr.history"
#     _rec_name='employee_id'
#     _order='change_date desc'
#     @api.multi
#     def draft(self):
#         self.write({'state':'draft'})
#     @api.multi
#     def confirm(self):
#         id=self.employee_id.id
#         self.write({'state':'confirm'})
#         obj=self.env['hr.employee'].search([('id','=',self.employee_id.id)])
#         obj.department_id=self.origin_dep_h
#         obj.job_id=self.origin_pos_h
#         objs=self.search([('employee_id','=',id),('id','!=',self.id)])
#         for op in objs:
#             op.update({'is_now': '2'})
#         products=self.search([('employee_id','=',id),('end_data','=',False),('id','!=',self.id)])
#         for product in products:
#             product.end_data=self.change_date
#         self.is_confirm=True
#
#
#
#     _columns = {
#         'employee_id': fields.many2one('hr.employee', u'员工'),
#         'change_date': fields.date(u'变更时间'),
#         'end_data':fields.date(u'结束时间'),
#         'origin_dep_q': fields.char(u'变更前部门'),
#         'origin_pos_q': fields.char(u'变更前职位'),
#         'origin_dep_h': fields.many2one('hr.department',u'变更后部门'),
#         'origin_pos_h': fields.many2one('hr.job',u'变更后职位'),
#         'change_reasion':fields.many2one('hr.chreasion',u'变更原因'),
#         'status':fields.selection([('up','升职'),('down','降职'),('change','调岗')],required=True,default='up',string='类型'),
#         'note':fields.text(u'备注'),
#         'state': fields.selection([
#                 ('draft', '草稿'),
#                 ('confirm', '确认'),
#             ],
#             string='State',
#             required=True,
#             default='draft'),
#         'is_now':fields.selection([('1','是'),('2','否')],u'是否当前',default='1'),
#         'is_confirm':fields.boolean(u'是否审核',default=False)
#     }
#
#     @api.onchange('employee_id')
#     def on_change(self):
#         dep=self.employee_id.department_id.name
#         pos=self.employee_id.job_id.name
#         self.origin_dep_q=dep
#         self.origin_pos_q=pos
#
#     @api.model
#     def create(self,vals):
#         if vals['employee_id']:
#             id=vals['employee_id']
#             dep=self.env['hr.employee'].search([('id','=',id)]).department_id.name
#             pos=self.env['hr.employee'].search([('id','=',id)]).job_id.name
#             vals.update(origin_dep_q=dep,origin_pos_q=pos)
#         return super(hr_history,self).create(vals)

    # @api.multi
    # def write(self,vals):
    #     id=vals['employee_id']
    #     dep=self.env['hr.employee'].search([('id','=',id)]).department_id.name
    #     pos=self.env['hr.employee'].search([('id','=',id)]).job_id.name
    #     vals.update(origin_dep_q=dep,origin_pos_q=pos)
    #     return super(hr_history,self).create(vals)


    # @api.model
    # def create(self,vals):
    #     id=vals['employee_id']
    #     obj=self.env['hr.employee'].search([('id','=',id)])
    #     if vals.get('origin_dep_h'):
    #         obj.department_id=vals['origin_dep_h']
    #     if vals.get('origin_pos_h'):
    #         obj.job_id=vals['origin_pos_h']
    #     objs=self.search([('employee_id','=',id)])
    #     for op in objs:
    #         op.update({'is_now': '2'})
    #     products=self.search([('employee_id','=',id),('end_data','=',False)])
    #     for  product in products:
    #         product.end_data=vals['change_date']
    #     result= super(hr_history,self).create(vals)
    #     return result
    # @api.multi
    # def write(self,vals):
    #     id= vals['employee_id']
    #     obj=self.env['hr.employee'].search([('id','=',id)])
    #     if vals.get('origin_dep_h'):
    #         obj.department_id=vals['origin_dep_h']
    #     if vals.get('origin_pos_h'):
    #         obj.job_id=vals['origin_pos_h']
    #     result= super(hr_history,self).create(vals)
    #     return result

# class hr_employee(osv.osv):
#     _inherit = 'hr.employee'
#     _columns={
#         'hr_history':fields.one2many('hr.history','employee_id',u'变更记录',domain=[('is_confirm','=',True)]),
#         'p_state':fields.selection([('inposition','在职'),('out','离职')],'在职状态',default='inposition')
#     }
#     @api.model
#     def create(self, vals):
#         if vals['department_id']:
#             origin_dep_q = '入职'
#             origin_dep_h = vals['department_id']
#         else:
#             origin_dep_q = '入职'
#             origin_dep_h = ''
#         if vals['job_id']:
#             origin_pos_q = '入职'
#             origin_pos_h = vals['job_id']
#         else:
#             origin_pos_q = '入职'
#             origin_pos_h = ''
#         newh = self.env['hr.history'].create({
#             'employee_id': self.id,
#             'origin_dep_q': origin_dep_q,
#             'origin_dep_h': origin_dep_h,
#             'origin_pos_q': origin_pos_q,
#             'origin_pos_h': origin_pos_h,
#             'change_date': time.strftime("%Y-%m-%d", time.localtime(time.time())),
#             'is_confirm':True,
#             'state':'confirm'
#         })
#         vals['hr_history']=newh
#         employee_id = super(hr_employee, self).create(vals)
#         newh.update({'employee_id': employee_id})
#         return employee_id



# class hr_goaway(osv.osv):
#     _name='hr.goaway'
#     _rec_name='employee_id'
#     _order='change_date desc'
#     @api.multi
#     def confirm(self):
#         id=self.employee_id.id
#         self.write({'state':'confirm'})
#         obj=self.env['hr.employee'].search([('id','=',self.employee_id.id)])
#         obj.p_state='out'
#         objs=self.env['hr.history'].search([('employee_id','=',id)])
#         for op in objs:
#             op.update({'is_now': '2'})
#         products=self.env['hr.history'].search([('employee_id','=',id),('end_data','=',False)])
#         for product in products:
#             product.end_data=self.change_date
#         self.is_confirm=True
#
#     _columns={
#         'employee_id': fields.many2one('hr.employee', u'员工'),
#         'change_date': fields.date(u'离职时间'),
#         'origin_dep_q': fields.char(u'部门'),
#         'origin_pos_q': fields.char(u'职位'),
#         'change_reasion':fields.many2one('hr.chreasion',u'离职原因'),
#         'note':fields.text(u'备注'),
#         'state': fields.selection([
#                 ('draft', '草稿'),
#                 ('confirm', '确认'),
#             ],
#             string='State',
#             required=True,
#             default='draft'),
#         'is_confirm':fields.boolean(u'是否审核',default=False)
#     }
#
#     @api.onchange('employee_id')
#     def on_change(self):
#         dep=self.employee_id.department_id.name
#         pos=self.employee_id.job_id.name
#         self.origin_dep_q=dep
#         self.origin_pos_q=pos
