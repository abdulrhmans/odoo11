# -*- coding: utf-8 -*-


from odoo import models, fields, api


class YcBusiness(models.Model):
    _name = "yc.customer"

    code = fields.Char("客戶編號")
    name = fields.Char("客戶名稱")


class YcProcessing(models.Model):
    _name = "yc.processing"

    code = fields.Char("加工廠編號")
    name = fields.Char("加工廠名稱")
    phone = fields.Char("電話")
    contact = fields.Char("負責人")