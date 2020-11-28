from odoo import models, fields, api
from odoo.exceptions import ValidationError

class DepositChequeWiz(models.TransientModel):
    _name = "cheque.deposit.wiz"

    cheque_id = fields.Many2one("account.cheque")
    journal_id = fields.Many2one("account.journal", "Journal")
    accounting_date = fields.Date("Accounting Date")

    @api.multi
    def action_apply_cheque(self):
        if self.cheque_id:
            self.cheque_id.journal_id = self.journal_id.id
            if self.cheque_id.accounting_date:
                if self.accounting_date < self.cheque_id.accounting_date:
                    raise ValidationError("Accounting date can`t be less than last cheque move date [%s].!" % (self.cheque_id.accounting_date))
            if self.accounting_date < self.cheque_id.payment_date:
                raise ValidationError("Accounting date can`t be less than payment date [%s].!" % (self.cheque_id.payment_date))
            self.cheque_id.accounting_date = self.accounting_date
            src = self._context.get('src')
            if src:
                if src == 'deposit_in_bank':
                    self.cheque_id.action_to_bank()
                elif src == 'withdrawal':
                    self.cheque_id.action_to_withdrawal()
                elif src == 'customer_bounced':
                    self.cheque_id.action_customer_bounced()
                elif src == 'vendor_bounced':
                    self.cheque_id.action_vendor_bounced()
                elif src == 'in_return':
                    self.cheque_id.action_return_inbound_to_account()
                elif src == 'out_return':
                    self.cheque_id.action_return_outbound_to_account()
                else:
                    raise ValidationError("Invalid cheque action. ")





