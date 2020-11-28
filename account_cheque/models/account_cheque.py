from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

CHEQUE_STATES = [('draft', 'Draft'),
                 ('under_collection', "Under Collection"),
                 ('out_standing', "Out Standing"),
                 ('in_bank', "In Bank"),
                 ('withdrawal', "Withdrawal"),
                 ('return_account', "Return To Account"),
                 ('in_bounced', "Bounced"),
                 ('out_bounced', "Bounced"),
                 ('done', 'Done')]

class AccountCheque(models.Model):
    _name = "account.cheque"
    _order = "id desc, date desc"

    name = fields.Char("Ref", required=1, default="NEW", readonly=1)
    payment_date = fields.Date("Payment Date", readonly=1)
    date = fields.Date("Date", required=1, readonly=1)
    journal_id = fields.Many2one("account.journal", string="Journal", readonly=1, required=1)
    bank_id = fields.Many2one("res.bank", "Bank")
    account_number = fields.Char()
    account_holder_id = fields.Many2one("res.partner", "Account Holder", readonly=1, required=1)
    beneficiary_id = fields.Many2one("res.partner", "Beneficiary", readonly=1)
    memo = fields.Text("Memo", readonly=1)
    amount = fields.Float("Amount", readonly=1)
    currency_id = fields.Many2one("res.currency", readonly=1)
    cheque_number = fields.Char("Cheque Number", Required=1, readonly=1)
    cheque_type = fields.Selection([('inbound', 'Inbound'), ('outbound', "Outbound")], readonly=1)
    state = fields.Selection(CHEQUE_STATES, default="draft", readonly=1)
    payment_id = fields.Many2one("account.payment", readonly=1)
    accounting_date = fields.Date("Accounting Date")
    cheque_line_ids = fields.One2many("account.cheque.line", "cheque_id", readonly=1)

    @api.model
    def create(self, vals):
        if 'name' not in vals or vals['name'] == _('New'):
            if 'cheque_type' in vals and vals['cheque_type'] == 'inbound':
                vals['name'] = self.env['ir.sequence'].next_by_code('in.cheque') or _('New')
            if 'cheque_type' in vals and vals['cheque_type'] == 'outbound':
                vals['name'] = self.env['ir.sequence'].next_by_code('out.cheque') or _('New')
        return super(AccountCheque, self).create(vals)

    @api.multi
    def action_to_under_collection(self):
        under_collection_account_id = self.journal_id.under_collection_account_id
        partner_id = self.account_holder_id
        if not under_collection_account_id:
            raise ValidationError("Please check under collection account.")
        if not partner_id.property_account_receivable_id:
            raise ValidationError("Please check partner receivable account.")
        desc = "STATUS: From Draft -> Under Collection"
        move_id = self.payment_id.move_line_ids and self.payment_id.move_line_ids[0].move_id
        line_vals = {'datetime': datetime.now(),
                     'desc': desc,
                     'move_id': move_id.id,
                     'cheque_id': self.id}
        self.env['account.cheque.line'].sudo().create(line_vals)
        self.state = "under_collection"

    @api.multi
    def action_to_bank(self):
        bank_account_id = self.journal_id.default_debit_account_id
        if self.state == 'under_collection':
            credit_account_id = self.journal_id.under_collection_account_id
            if not credit_account_id:
                raise ValidationError("Please check under collection account.")
            desc = "STATUS: From Under Collection -> Bank"
        if self.state == 'in_bounced':
            credit_account_id = self.journal_id.customer_bounced_account_id
            if not credit_account_id:
                raise ValidationError("Please check customer bounced account.")
            desc = "STATUS: From Bounced -> Bank"
        partner_id = self.account_holder_id
        if not bank_account_id:
            raise ValidationError("Please check bank account.")

        amount = self.amount
        move_vals = {'journal_id': self.journal_id.id,
                     'date': self.accounting_date or datetime.today(),
                     'ref': self.name,
                     'line_ids': [(0, 0, {'account_id': bank_account_id.id,
                                          'name': self.name + '[' + desc + ']',
                                          'partner_id': partner_id.id,
                                          'debit': amount,
                                          'credit': 0.0}),
                                  (0, 0, {'account_id': credit_account_id.id,
                                          'name': self.name + '[' + desc + ']',
                                          'partner_id': partner_id.id,
                                          'debit': 0.0,
                                          'credit': amount})]}
        move_id = self.env['account.move'].sudo().create(move_vals)
        move_id.sudo().action_post()
        line_vals = {'datetime': datetime.now(),
                     'desc': desc,
                     'move_id': move_id.id,
                     'cheque_id': self.id}
        self.env['account.cheque.line'].sudo().create(line_vals)
        self.state = "in_bank"

    @api.multi
    def action_to_out_standing(self):
        out_standing_account_id = self.journal_id.out_standing_account_id
        partner_id = self.account_holder_id
        if not out_standing_account_id:
            raise ValidationError("Please check out standing account.")
        if not partner_id.property_account_payable_id:
            raise ValidationError("Please check partner payable account.")
        desc = "STATUS: From Draft -> Out Standing"
        move_id = self.payment_id.move_line_ids and self.payment_id.move_line_ids[0].move_id
        line_vals = {'datetime': datetime.now(),
                     'desc': desc,
                     'move_id': move_id.id,
                     'cheque_id': self.id}
        self.env['account.cheque.line'].sudo().create(line_vals)
        self.state = 'out_standing'

    @api.multi
    def action_to_withdrawal(self):
        bank_account_id = self.journal_id.default_credit_account_id
        if self.state == 'out_standing':
            debit_account_id = self.journal_id.out_standing_account_id
            if not debit_account_id:
                raise ValidationError("Please check out standing account.")
            desc = "STATUS: From Out Standing -> Withdrawal"
        if self.state == 'out_bounced':
            debit_account_id = self.journal_id.vendor_bounced_account_id
            if not debit_account_id:
                raise ValidationError("Please check vendor bounced account.")
            desc = "STATUS: From Bounced -> Withdrawal"
        partner_id = self.account_holder_id
        if not bank_account_id:
            raise ValidationError("Please check bank account.")

        amount = self.amount
        move_vals = {'journal_id': self.journal_id.id,
                     'date': self.accounting_date or datetime.today(),
                     'ref': self.name,
                     'line_ids': [(0, 0, {'account_id': debit_account_id.id,
                                          'name': self.name + '[' + desc + ']',
                                          'partner_id': partner_id.id,
                                          'debit': amount,
                                          'credit': 0.0}),
                                  (0, 0, {'account_id': bank_account_id.id,
                                          'name': self.name + '[' + desc + ']',
                                          'partner_id': partner_id.id,
                                          'debit': 0.0,
                                          'credit': amount})]}
        move_id = self.env['account.move'].sudo().create(move_vals)
        move_id.sudo().action_post()
        line_vals = {'datetime': datetime.now(),
                     'desc': desc,
                     'move_id': move_id.id,
                     'cheque_id': self.id}
        self.env['account.cheque.line'].sudo().create(line_vals)
        self.state = "withdrawal"

    @api.multi
    def action_customer_bounced(self):
        if self.cheque_type == 'inbound':
            debit_account_id = self.journal_id.customer_bounced_account_id
            if not debit_account_id:
                raise ValidationError("Please check customer bounced account.")
            if self.state == 'under_collection':
                credit_account_id = self.journal_id.under_collection_account_id
                desc = "STATUS: From Under Collection -> Bounced"
                if not credit_account_id:
                    raise ValidationError("Please check under collection account.")
            if self.state == 'in_bank':
                credit_account_id = self.journal_id.default_credit_account_id
                desc = "STATUS: From Bank -> Bounced"
                if not credit_account_id:
                    raise ValidationError("Please check journal credit account.")
        partner_id = self.account_holder_id
        amount = self.amount
        move_vals = {'journal_id': self.journal_id.id,
                     'date': self.accounting_date or datetime.today(),
                     'ref': self.name,
                     'line_ids': [(0, 0, {'account_id': debit_account_id.id,
                                          'name': self.name + '[' + desc + ']',
                                          'partner_id': partner_id.id,
                                          'debit': amount,
                                          'credit': 0.0}),
                                  (0, 0, {'account_id': credit_account_id.id,
                                          'name': self.name + '[' + desc + ']',
                                          'partner_id': partner_id.id,
                                          'debit': 0.0,
                                          'credit': amount})]}
        move_id = self.env['account.move'].sudo().create(move_vals)
        move_id.sudo().action_post()
        line_vals = {'datetime': datetime.now(),
                     'desc': desc,
                     'move_id': move_id.id,
                     'cheque_id': self.id}
        self.env['account.cheque.line'].sudo().create(line_vals)
        self.state = "in_bounced"

    @api.multi
    def action_vendor_bounced(self):
        if self.cheque_type == 'outbound':
            credit_account_id = self.journal_id.vendor_bounced_account_id
            if not credit_account_id:
                raise ValidationError("Please check vendor bounced account.")
            if self.state == 'out_standing':
                debit_account_id = self.journal_id.out_standing_account_id
                desc = "STATUS: From Out Standing -> Bounced"
                if not debit_account_id:
                    raise ValidationError("Please check Out Standing account.")
            if self.state == 'withdrawal':
                debit_account_id = self.journal_id.default_debit_account_id
                desc = "STATUS: From Withdrawal -> Bounced"
                if not debit_account_id:
                    raise ValidationError("Please check journal debit account.")
        partner_id = self.account_holder_id
        amount = self.amount
        move_vals = {'journal_id': self.journal_id.id,
                     'date': self.accounting_date or datetime.today(),
                     'ref': self.name,
                     'line_ids': [(0, 0, {'account_id': debit_account_id.id,
                                          'name': self.name + '[' + desc + ']',
                                          'partner_id': partner_id.id,
                                          'debit': amount,
                                          'credit': 0.0}),
                                  (0, 0, {'account_id': credit_account_id.id,
                                          'name': self.name + '[' + desc + ']',
                                          'partner_id': partner_id.id,
                                          'debit': 0.0,
                                          'credit': amount})]}
        move_id = self.env['account.move'].sudo().create(move_vals)
        move_id.sudo().action_post()
        line_vals = {'datetime': datetime.now(),
                     'desc': desc,
                     'move_id': move_id.id,
                     'cheque_id': self.id}
        self.env['account.cheque.line'].sudo().create(line_vals)
        self.state = "out_bounced"

    @api.multi
    def action_return_inbound_to_account(self):
        debit_account_id = self.account_holder_id.property_account_receivable_id
        if not debit_account_id:
            raise ValidationError("Please check partner receivable account.")
        credit_account_id = self.journal_id.under_collection_account_id
        desc = "STATUS: From Under Collection -> Return To Account"
        if self.state == 'in_bank':
            credit_account_id = self.journal_id.default_credit_account_id
            desc = "STATUS: From Bank -> Return To Account"
        if not credit_account_id:
            raise ValidationError("Please check credit account.")

        partner_id = self.account_holder_id
        amount = self.amount
        move_vals = {'journal_id': self.journal_id.id,
                     'date': self.accounting_date or datetime.today(),
                     'ref': self.name,
                     'line_ids': [(0, 0, {'account_id': debit_account_id.id,
                                          'name': self.name + '[' + desc + ']',
                                          'partner_id': partner_id.id,
                                          'debit': amount,
                                          'credit': 0.0}),
                                  (0, 0, {'account_id': credit_account_id.id,
                                          'name': self.name + '[' + desc + ']',
                                          'partner_id': partner_id.id,
                                          'debit': 0.0,
                                          'credit': amount})]}
        move_id = self.env['account.move'].sudo().create(move_vals)
        move_id.sudo().action_post()
        line_vals = {'datetime': datetime.now(),
                     'desc': desc,
                     'move_id': move_id.id,
                     'cheque_id': self.id}
        self.env['account.cheque.line'].sudo().create(line_vals)
        self.state = "return_account"

    @api.multi
    def action_return_outbound_to_account(self):
        credit_account_id = self.account_holder_id.property_account_payable_id
        if not credit_account_id:
            raise ValidationError("Please check partner payable account.")
        debit_account_id = self.journal_id.out_standing_account_id
        desc = "STATUS: From Outstanding -> Return To Account"
        if self.state == 'withdrawal':
            debit_account_id = self.journal_id.default_debit_account_id
            desc = "STATUS: From Withdrawal -> Return To Account"
        if not debit_account_id:
            raise ValidationError("Please check debit account.")

        partner_id = self.account_holder_id
        amount = self.amount
        move_vals = {'journal_id': self.journal_id.id,
                     'date': self.accounting_date or datetime.today(),
                     'ref': self.name,
                     'line_ids': [(0, 0, {'account_id': debit_account_id.id,
                                          'name': self.name + '[' + desc + ']',
                                          'partner_id': partner_id.id,
                                          'debit': amount,
                                          'credit': 0.0}),
                                  (0, 0, {'account_id': credit_account_id.id,
                                          'name': self.name + '[' + desc + ']',
                                          'partner_id': partner_id.id,
                                          'debit': 0.0,
                                          'credit': amount})]}
        move_id = self.env['account.move'].sudo().create(move_vals)
        move_id.sudo().action_post()
        line_vals = {'datetime': datetime.now(),
                     'desc': desc,
                     'move_id': move_id.id,
                     'cheque_id': self.id}
        self.env['account.cheque.line'].sudo().create(line_vals)
        self.state = "return_account"

    @api.multi
    def action_to_done(self):
        if self.state == 'in_bank':
            desc = "STATUS: From Bank -> Done"
        if self.state == 'in_bounced':
            desc = "STATUS: From Bounced -> Done"
        if self.cheque_type == 'outbound':
            if self.state == 'withdrawal':
                desc = "STATUS: From Withdrawal -> Done"
            if self.state == 'out_bounced':
                desc = "STATUS: From Bounced -> Done"
        line_vals = {'datetime': datetime.now(),
                     'desc': desc,
                     'cheque_id': self.id}
        self.env['account.cheque.line'].sudo().create(line_vals)
        self.state = "done"

class AccountChequeLines(models.Model):
    _name = "account.cheque.line"
    _order = "id desc, datetime desc"

    datetime = fields.Datetime("Time", readonly=1)
    desc = fields.Text("Description", readonly=1, required=1)
    move_id = fields.Many2one("account.move", "Move", readonly=1)
    cheque_id = fields.Many2one("account.cheque", readonly=1)





