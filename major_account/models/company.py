# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountSettings(models.Model):
    _inherit = 'res.company'

    major_account_prefix = fields.Char(string='Prefix')
    major_account_seperator = fields.Char(string='Seperator', size=1, default ='')
    major_accounts_levels = fields.Integer(string='No of Max level', default=5)
    account_code_length = fields.Integer(string='Chart of Account Code Length', default=3)
    major_account_level_setup = fields.One2many('account.major.level', 'company_id',
                                                  string='major Account Level Setup')
    major_accounts = fields.One2many('account.major', 'company_id',
                                       string='Major Accounts')

    @api.multi
    def generate_levels(self):
        if not self.major_accounts_levels > 0:
            raise UserError(_('Please select no of Max level!'))
            return
        self.major_account_level_setup.unlink()
        for level in xrange(self.major_accounts_levels):
            self.major_account_level_setup.create(
                {'name': str(level + 1), 'level': level, 'code_length': level < 2 and level + 1 or 3,
                 'company_id': self.id})
        self.major_accounts.update_accounts_code()

    @api.multi
    @api.depends('major_account_prefix', 'major_accounts_levels', 'major_account_level_setup')
    def generate_major_accounts_from_template(self):
        def create_child(account, parent_id):
            new_account = self.major_accounts.create(
                {'name': account.name, 'company_id': self.id, 'description': account.description,
                 'parent_id': parent_id,
                 'is_leaf': account.is_leaf})
            if account.child_ids:
                for child_account in account.child_ids:
                    create_child(child_account, new_account.id)

        template_accounts_list = self.env['account.major.template'].search([])
        if template_accounts_list.get_max_level() > self.major_accounts_levels:
            raise UserError(_("Template Max level(" + str(template_accounts_list.get_max_level()) +
                              ") is greater than configured max level for this company"))
            return
        if len(self.major_account_level_setup) < self.major_accounts_levels:
            raise UserError(_("Please Generate levels and setup code length for each level first!!"))
            return

        self.major_accounts.search([('company_id', '=', self.id)]).unlink()
        for template_account in template_accounts_list.search([('parent_id', '=', None)]):
            create_child(template_account, False)

    @api.multi
    def write(self, vals):
        super_result = super(AccountSettings, self).write(vals)
        for company in self:
            if 'major_account_prefix' in vals or 'account_code_length' in vals or 'major_account_level_setup' in vals:
                company.major_accounts.update_accounts_code()

        return super_result
