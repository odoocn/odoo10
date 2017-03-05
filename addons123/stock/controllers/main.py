# -*- coding: utf-8 -*-
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class BarcodeController(http.Controller):

    @http.route(['/stock/barcode/'], type='http', auth='user')
    def a(self, debug=False, **k):
        if not request.session.uid:
            return http.local_redirect('/web/login?redirect=/stock/barcode/')

        return request.render('stock.barcode_index')

    @http.route('/weixin/test', type='http', auth='user', csrf=False)
    def weixin_test(self, **post):

        http = request.httprequest
        logging.error("http: %s", str(http))
        signature = post.get("signature", None)
        echostr = post.get("echostr", None)
        timestamp = post.get("timestamp", None)
        nonce = post.get("nonce", None)
        _logger.log("signature: %s", signature)
        _logger.log("echostr: %s", echostr)
        _logger.log("timestamp: %s", timestamp)
        _logger.log("nonce: %s", nonce)
        html = request.httprequest.data
        _logger.error("html: %s", html)
        return html