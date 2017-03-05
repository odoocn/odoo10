# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError
from odoo.modules.module import get_module_resource
import logging
import base64
import odoo

_logger = logging.getLogger(__name__)


class AppUpdate(models.Model):
    _name = "app.update"

    name = fields.Char(string=u'名称', required=True)
    boundleID = fields.Char(string=u'app唯一标识', required=True)
    version = fields.Char(string=u'版本号', required=True)
    platform = fields.Selection([('ios', 'IOS'), ('android', 'Android')], string=u'平台', required=True)
    url = fields.Char(string=u'下载地址')
    describe = fields.Text(string=u'更新内容')
    size = fields.Float(string=u'更新包大小(字节)', readonly=True)
    update_time = fields.Datetime(string=u'更新日期', required=True)
    app_file_name = fields.Char(string=u'文件名')
    app = fields.Binary(u"更新包", attachment=True)
    editable = fields.Boolean(default=True)

    image = fields.Binary("Photo", attachment=True,
                                  help="This field holds the image used as photo for the employee, limited to 1024x1024px.")
    image_medium = fields.Binary("Medium-sized photo", attachment=True,
                                         help="Medium-sized photo of the employee. It is automatically " \
                                              "resized as a 128x128px image, with aspect ratio preserved. " \
                                              "Use this field in form views or some kanban views.")
    image_small = fields.Binary("Small-sized photo", attachment=True,
                                        help="Small-sized photo of the employee. It is automatically " \
                                             "resized as a 64x64px image, with aspect ratio preserved. " \
                                             "Use this field anywhere a small image is required.")

    def _get_default_image(self, cr, uid, context=None):
        image_path = get_module_resource('apk_upload', 'static/img', 'icon.png')
        return tools.image_resize_image_big(open(image_path, 'rb').read().encode('base64'))

    defaults = {
        'image': _get_default_image,
    }

    @api.multi
    def write(self, vals):
        tools.image_resize_images(vals)
        return super(AppUpdate, self).write(vals)

    def unlink(self, cr, uid, ids, context=None):
        raise UserError(_("不可删除"))

    @api.model
    def create(self, vals):
        if self.search([('boundleID', '=', vals['boundleID']), ('platform', '=', vals['platform'])]):
            raise UserError(_('同一平台下APP标识不可重复'))
        vals['size'] = len(base64.b64decode(vals['app']))
        vals['editable'] = False
        tools.image_resize_images(vals)
        app = super(AppUpdate, self).create(vals)
        app.write({'url': odoo.tools.config['server_host'] + '/web/content/app.update/' + str(app.id) + '/app/' + app.app_file_name})
        return app
