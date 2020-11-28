from odoo import models, fields, api

class ResBank(models.Model):
    _inherit = "res.bank"

    account_holder_w = fields.Float("Holder Width", default=100)
    account_holder_h = fields.Float("Holder Height", default=10)
    account_holder_x = fields.Float("Holder Top-M", default=10)
    account_holder_y = fields.Float("Holder Left-M", default=10)

    date_w = fields.Float("Date Width", default=100)
    date_h = fields.Float("Date Height", default=10)
    date_x = fields.Float("Date Top-M", default=10)
    date_y = fields.Float("Date Left-M", default=10)

    amount_w = fields.Float("Amount Width", default=100)
    amount_h = fields.Float("Amount Height", default=10)
    amount_x = fields.Float("Amount Top-M", default=10)
    amount_y = fields.Float("Amount Left-M", default=10)

    desc_w = fields.Float("Description Width", default=100)
    desc_h = fields.Float("Description Height", default=10)
    desc_x = fields.Float("Description Top-M", default=10)
    desc_y = fields.Float("Description Left-M", default=10)

    cheque_w = fields.Float("Cheque Width", default=30)
    cheque_h = fields.Float("Cheque Height", default=10)
