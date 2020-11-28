from odoo import models, fields, api
from odoo.exceptions import  ValidationError

class AccountPayment(models.Model):
    _inherit = "account.payment"

    cheque_no = fields.Char("Cheque No")
    bank_id = fields.Many2one("res.bank", "Bank")
    cheque_date = fields.Date("Cheque Date")
    account_no = fields.Char("Account No")
    cheque_id = fields.Many2one("account.cheque")

    @api.onchange('journal_id')
    def get_cheque_no(self):
        for rec in self:
            if rec.payment_type == 'outbound':
                if rec.journal_id:
                    rec.cheque_no = int(rec.journal_id.cheque_no) + 1

    def _get_liquidity_move_line_vals(self, amount):
        res = super(AccountPayment, self)._get_liquidity_move_line_vals(amount)
        if self.payment_type == 'inbound' and self.payment_method_code == 'cheque':
            # compute debit account
            res['account_id'] = self.journal_id.under_collection_account_id.id
        if self.payment_type == 'outbound' and self.payment_method_code == 'cheque':
            res['account_id'] = self.journal_id.out_standing_account_id.id
        return res

    @api.multi
    def post(self):
        for rec in self:
            if rec.payment_type in ['inbound', 'outbound'] and rec.payment_method_code == 'cheque':
                if rec.payment_type == 'outbound':
                    rec.journal_id.cheque_no = rec.cheque_no
                if self.cheque_date and self.payment_date:
                    if self.payment_date > self.cheque_date:
                        raise ValidationError("Sorry: Cheque date can`t be less than payment date.")
                cheque_info = {'payment_date': rec.payment_date,
                               'cheque_type': 'inbound' if rec.payment_type == 'inbound' else 'outbound',
                               'date': rec.cheque_date,
                               'journal_id': rec.journal_id.id,
                               'account_holder_id': rec.partner_id.id,
                               'beneficiary_id': self.env.user.company_id.partner_id.id,
                               'memo': rec.communication,
                               'amount': rec.amount,
                               'currency_id': rec.currency_id.id,
                               'cheque_number': rec.cheque_no,
                               'bank_id': rec.bank_id.id,
                               'account_number': rec.account_no,
                               'payment_id': rec.id,
                               }
                cheque_id = self.env['account.cheque'].sudo().create(cheque_info)
                res = super(AccountPayment, self).post()
                if cheque_id and self.id:
                    self.cheque_id = cheque_id.id
                if rec.payment_type == 'inbound':
                    cheque_id.with_context({'without_move': True}).action_to_under_collection()
                if rec.payment_type == 'outbound':
                    cheque_id.with_context({'without_move': True}).action_to_out_standing()
                return res
        return super(AccountPayment, self).post()
