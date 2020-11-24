# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import datetime, date
from odoo.exceptions import UserError


class Account(models.Model):
    _inherit = 'account.account'

    @api.multi
    def get_move_lines_on_period(self, from_date=False, to_date=False, move_type="all"):
        """ return move lines for accounts
        if no from_date: period starts with beginning of year for P/L accounts, and no starting point for BL accounts
        if no to_date: period ends with today's date
        """
        if not to_date:
            to_date = date.today()
        move_line_obj = self.env['account.move.line']
        account_ids = self.mapped('id')
        state = ['draft', 'posted'] if move_type == 'all' else ['posted']
        if not from_date:
            from_date = str(
                date.today().replace(day=1, month=1))  # beginning of the current  year, used for profit/loss accounts
            move_lines = move_line_obj.search([
                ('account_id', 'in', account_ids), ('date', '<=', to_date), ('move_id.state', 'in', state), "|",
                ('account_id.user_type_id.include_initial_balance', '=', True), "&",
                ('account_id.user_type_id.include_initial_balance', '=', False), ('date', '>=', from_date)
            ])
        else:
            move_lines = move_line_obj.search([
                ('account_id', 'in', account_ids), ('date', '<=', to_date), ('date', '>=', from_date),
                ('move_id.state', 'in', state)])
        return move_lines

    @api.multi
    def get_debit_on_date(self, to_date=False, move_type="all"):
        """ returns only debit """
        move_lines = self.get_move_lines_on_period(to_date=to_date, move_type=move_type)
        total_debit = move_lines and sum(move_lines.mapped("debit")) or 0
        return total_debit

    @api.multi
    def get_credit_on_date(self, to_date=False, move_type="all"):
        """ returns only credit """
        move_lines = self.get_move_lines_on_period(to_date=to_date, move_type=move_type)
        total_credit = move_lines and sum(move_lines.mapped("credit")) or 0
        return total_credit

    @api.multi
    def get_credit_total(self, balance_date=None, balance_type='posted'):
        if balance_date is None:
            balance_date = datetime.now()
        move_states = ['posted']
        if balance_type != 'posted':
            move_states.append('draft')
        move_lines = self.env['account.move.line'].search(
            [('account_id', 'in', self.ids), ('move_id.state', 'in', move_states), ('move_id.date', '<=', balance_date)])
        credit_total = 0
        for line in move_lines:
            credit_total += line.credit
        return credit_total

    @api.multi
    def get_debit_total(self, balance_date=None, balance_type='posted'):
        if balance_date is None:
            balance_date = datetime.now()
        move_states = ['posted']
        if balance_type != 'posted':
            move_states.append('draft')
        move_lines = self.env['account.move.line'].search(
            [('account_id', 'in', self.ids), ('move_id.state', 'in', move_states),
             ('move_id.date', '<=', balance_date)])
        debit_total = 0
        for line in move_lines:
            debit_total += line.debit
        return debit_total

    @api.multi
    def compute_balance(self, balance_date=None, balance_type='posted'):
        for rec in self:
            total_debit = rec.get_debit_total(balance_date, balance_type)
            total_credit = rec.get_credit_total(balance_date, balance_type)
            rec.balance = total_debit - total_credit

    @api.multi
    def _balance(self):
        for rec in self:
            rec.balance = rec.get_debit_total()- rec.get_credit_total()

    major_account_id = fields.Many2one("account.major", string="Major Account",
                                       ondelete="set null", domain=lambda self:[('is_leaf', '=', True), ('company_id', '=', self.env.user.company_id.id), '|', ('company_id', '=', False)])
    balance = fields.Float(string="Balance", compute='_balance')

    @api.onchange('major_account_id')
    def set_account_code(self):
        self.ensure_one()
        def is_int(x):
            try:
                int(x)
                return True
            except ValueError:
                return False
        if not self.major_account_id.id:
            return
        company_conf = self.env['res.company'].search([('id', '=', self.company_id.id)])
        acc_code_length = company_conf.account_code_length
        seperator =str(company_conf.major_account_seperator and company_conf.major_account_seperator or '')
        # major_account_code = self.major_account_id.code_get()
        brothers_rec_set = self.env['account.account'].search(
            [('major_account_id', '=', self.major_account_id.id),
             ('id', '!=', self.id and self.id or 0)]).mapped('code')
        brothers_int_codes = [int(bro[-1 * acc_code_length:]) if is_int(bro[-1 * acc_code_length:]) else 0  for bro in brothers_rec_set]
        code = 1
        code_found = False
        while not code_found:
            if code in brothers_int_codes:
                code += 1
            else:
                code_found = True
        code = str(code)
        for i in xrange(acc_code_length - len(code)):
            code = '0' + code
        major_account_code = self.major_account_id.code_get()
        major_account_str_code = str(major_account_code[0][1])
        new_code = major_account_str_code + seperator + code
        self.code = new_code

    @api.multi
    def write(self, vals):
        if 'major_account_id' in vals:
            if vals['major_account_id']:
                major_account = self.env['account.major'].browse(vals['major_account_id'])
                if not major_account.is_leaf:
                    raise UserError(_("Can't link account to non-leaf major account!!"))
                    return
        super_result = super(Account, self).write(vals)
        return super_result
