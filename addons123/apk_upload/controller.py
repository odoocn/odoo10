# -*- coding: utf-8 -*-
import logging
import odoo
from odoo import http
from odoo.http import request

logger = logging.getLogger(__name__)


class ApkUpload(odoo.addons.web.controllers.main.Home):
    #------------------------------------------------------
    # View
    #------------------------------------------------------
    @http.route('/download', type='http', auth='public', website=True)
    def download(self, **kw):
        result = []
        for app in request.env['app.update'].search([]):
            result.append({'name': app.name,
                           'url': app.url,
                           'description': app.describe,
                           'img_url': "/web/image?model=app.update&field=image_small&id=" + str(app.id)})
        return request.render('apk_upload.website_download', {'result': result})
