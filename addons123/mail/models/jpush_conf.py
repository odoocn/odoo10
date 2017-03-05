# -*- coding: utf-8 -*-
# please put your app_key and master_secret here
# app_key = u'6bc3b739cb16fb8cfefa86d5'
# master_secret = u'b80bf78d3bc97f2396d7b3bb'

from odoo import fields, models


class JpushConf(models.Model):
    _name = "jpush.conf"

    app_key = fields.Char("appKey")
    master_secret = fields.Char("masterSecret")