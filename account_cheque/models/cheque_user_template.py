from odoo import models, fields, api

class ChequeUserTemplate(models.Model):
    _name = "cheque.user.template"

    name = fields.Char("Template Name", required=1)
    bank_id = fields.Many2one("res.bank", "Bank", required=1)
    account_holder_w = fields.Float("Holder Width")
    account_holder_h = fields.Float("Holder Height")
    account_holder_x = fields.Float("Holder Top-M")
    account_holder_y = fields.Float("Holder Left-M")
    date_w = fields.Float("Date Width")
    date_h = fields.Float("Date Height")
    date_x = fields.Float("Date Top-M")
    date_y = fields.Float("Date Left-M")
    amount_w = fields.Float("Amount Width")
    amount_h = fields.Float("Amount Height")
    amount_x = fields.Float("Amount Top-M")
    amount_y = fields.Float("Amount Left-M")
    desc_w = fields.Float("Description Width")
    desc_h = fields.Float("Description Height")
    desc_x = fields.Float("Description Top-M")
    desc_y = fields.Float("Description Left-M")
    cheque_w = fields.Float("Cheque Width")
    cheque_h = fields.Float("Cheque Height")

    @api.onchange('bank_id')
    def set_default_bank_data(self):
        if self.bank_id:
            if not self.cheque_w:
                self.cheque_w = self.bank_id.cheque_w
            if not self.cheque_h:
                self.cheque_h = self.bank_id.cheque_h
            if not self.account_holder_w:
                self.account_holder_w = self.bank_id.account_holder_w
            if not self.account_holder_h:
                self.account_holder_h = self.bank_id.account_holder_h
            if not self.account_holder_x:
                self.account_holder_x = self.bank_id.account_holder_x
            if not self.account_holder_y:
                self.account_holder_y = self.bank_id.account_holder_y

            if not self.date_w:
                self.date_w = self.bank_id.date_w
            if not self.date_h:
                self.date_h = self.bank_id.date_h
            if not self.date_x:
                self.date_x = self.bank_id.date_x
            if not self.date_y:
                self.date_y = self.bank_id.date_y

            if not self.amount_w:
                self.amount_w = self.bank_id.amount_w
            if not self.amount_h:
                self.amount_h = self.bank_id.amount_h
            if not self.amount_x:
                self.amount_x = self.bank_id.amount_x
            if not self.amount_y:
                self.amount_y = self.bank_id.amount_y

            if not self.desc_w:
                self.desc_w = self.bank_id.desc_w
            if not self.desc_h:
                self.desc_h = self.bank_id.desc_h
            if not self.desc_x:
                self.desc_x = self.bank_id.desc_x
            if not self.desc_y:
                self.desc_y = self.bank_id.desc_y
