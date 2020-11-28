from odoo import models, fields, api

class AccountJournal(models.Model):
    _inherit = "account.journal"

    under_collection_account_id = fields.Many2one('account.account', "Under Collection Account")
    out_standing_account_id = fields.Many2one('account.account', "Out Standing Account")
    customer_bounced_account_id = fields.Many2one("account.account", "Customer Bounced Account")
    vendor_bounced_account_id = fields.Many2one("account.account", "Vendor Bounced Account")
    is_inbound_cheque = fields.Boolean("Is Inbound Cheque", compute="check_payment_method_selection")
    is_outbound_cheque = fields.Boolean("Is Outbound Cheque", compute="check_payment_method_selection")
    cheque_no = fields.Char("Cheque No")

    @api.depends("inbound_payment_method_ids", "outbound_payment_method_ids")
    def check_payment_method_selection(self):
        for rec in self:
            for payment_method in rec.inbound_payment_method_ids:
                if payment_method.name == 'Cheque':
                    rec.is_inbound_cheque = True
            for payment_method in rec.outbound_payment_method_ids:
                if payment_method.name == 'Cheque':
                    rec.is_outbound_cheque = True
