# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.osv import expression
from odoo.exceptions import  ValidationError,UserError,Warning

from datetime import date, datetime
from dateutil.relativedelta import relativedelta


class AccountMajor(models.Model):
    _name = 'account.major'

    @api.one
    def name_get(self):
        # self.ensure_one()
        def get_names(major_account):
            """ Return the list [account_major.name, account_major.parent_id.name, ...] """
            res = []
            while major_account:
                if major_account.parent_id:
                    res.append(major_account.name and major_account.name or '---')
                major_account = major_account.parent_id

            return res
        seperator = self.env.user.company_id.major_account_seperator or ''
        prefix_account = self.env.user.company_id.major_account_prefix
        seperator = seperator if seperator else '/'
        names = [(account.id, account.name and
                  ((str(account.company_id.major_account_prefix) and
                    str(account.company_id.major_account_prefix or prefix_account) + seperator or
                    str(account.company_id.name) + seperator) + seperator.join(reversed(get_names(account))) +
                   ' ' + str((account.description and account.description or ''))) or '') for account in self]
        return names[0]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if not args:
            args = []
        if name:
            codes = name.split(' / ')
            parents = list(codes)
            child = parents.pop()
            domain = ['|', ('description', operator, child), ('name', operator, name)]
            if parents:
                names_ids = self.name_search(' / '.join(parents), args=args, operator='ilike', limit=limit)
                loc_ids = [name_id[0] for name_id in names_ids]
                if operator in expression.NEGATIVE_TERM_OPERATORS:
                    locs = self.search([('id', 'not in', loc_ids)])
                    domain = expression.OR([[('parent_id', 'in', locs.ids)], domain])
                else:
                    domain = expression.AND([[('parent_id', 'in', loc_ids)], domain])
                for i in range(1, len(codes)):
                    domain = [[('complete_code', operator, ' / '.join(codes[-1 -i:]))], domain]
                    if operator in expression.NEGATIVE_TERM_OPERATORS:
                         domain = expression.AND(domain)
                    else:
                        domain = expression.OR(domain)
            ids = self.search(expression.AND([domain, args]), limit=limit)
        else:
            ids = self.search(args, limit=limit)
        return ids.name_get()

    @api.depends('name', 'parent_id')
    def _name_get_fnc(self):
        for rec in self:
            rec.complete_name = rec.name_get()[0]

    @api.multi
    def code_get(self):
        def get_code(daccount):
            """ Return the list [account_major.name, account_major.parent_id.name, ...] """
            res = []
            while daccount:
                res.append(daccount.name and daccount.name or '---')
                daccount = daccount.parent_id
            return res
        names = [(account.id, account.name and
                  ((self.env.user.company_id.major_account_prefix and
                    self.env.user.company_id.major_account_prefix or
                    self.env.user.company_id.name) + ''.join(reversed(get_code(account)))) or '') for account in self]
        return names

    @api.depends('name', 'parent_id')
    def _code_get_fnc(self):
        for rec in self:
            rec.complete_code = rec.code_get()[0][1]

    @api.multi
    def get_total_credit(self):
        credit_list = []
        for rec in self:
            total_credit = 0
            if rec.is_leaf:
                for account in rec.accounts:
                    total_credit += account.get_credit_on_date(to_date=rec.balance_date, move_type=rec.balance_type)
            else:
                if rec.child_ids:
                    for child_account in rec.child_ids:
                        child_account.balance_start_date = rec.balance_start_date
                        child_account.balance_date = rec.balance_date
                        child_account.balance_type = rec.balance_type
                        total_credit+=child_account.get_total_credit()[0][1]
                else:
                    total_credit = 0
            credit_list.append([rec.id, total_credit])
        return credit_list

    @api.multi
    def get_total_debit(self):
        debit_list = []
        for rec in self:
            total_debit = 0.0
            if rec.is_leaf:
                for account in rec.accounts:
                    total_debit += account.get_debit_on_date(to_date=rec.balance_date, move_type=rec.balance_type)
            else:
                if rec.child_ids:
                    for child_account in rec.child_ids:
                        child_account.balance_start_date = rec.balance_start_date
                        child_account.balance_date = rec.balance_date
                        child_account.balance_type = rec.balance_type
                        total_debit = total_debit + child_account.get_total_debit()[0][1]
                else:
                    total_debit = 0
            debit_list.append([rec.id, total_debit])
        return debit_list

    @api.multi
    @api.model
    def update_accounts_code(self):
        for rec in self:
            if rec.is_leaf:
                for account in rec.accounts:
                    account.set_account_code()
                    # account.write({'code': account.code})
            else:
                if rec.child_ids:
                    for child_account in rec.child_ids:
                        child_account.complete_code = child_account.code_get()[0][1]
                        child_account.complete_name = child_account.name_get()[0][1]
                        ##child_account.onchange_parent()
                        child_account.update_accounts_code()

    @api.multi
    @api.model
    def update_accounts_multi(self):
        for rec in self:
            rec.name = rec.get_account_code()
            rec._code_get_fnc()
            rec._name_get_fnc()
        self.update_accounts_code()

    @api.multi
    @api.depends('balance_date', 'balance_type', 'balance_start_date')
    def _total_credit(self):
        for rec in self:
            rec.total_credit = rec.get_total_credit()[0][1]

    @api.multi
    @api.depends('balance_date', 'balance_type', 'balance_start_date')
    def _total_debit(self):
        for rec in self:
            rec.total_debit = rec.get_total_debit()[0][1]

    def _credit_balance(self):
        for rec in self:
            rec.credit_balance = (rec.total_debit - rec.total_credit) < 0 and (rec.total_debit - rec.total_credit) * -1 or 0

    def _debit_balance(self):
        for rec in self:
            rec.debit_balance = (rec.total_debit - rec.total_credit) > 0 and (rec.total_debit - rec.total_credit) or 0

    @api.depends('balance_date', 'balance_type', 'balance_start_date')
    def _balance(self):
        for rec in self:
            rec.balance = rec.total_debit - rec.total_credit

    def _balance_date(self):
        for rec in self:
            if not rec.balance_date:
                rec.balance_date = date.today()

    @api.depends('parent_id')
    def _get_account_level(self):
        for rec in self:
            rec.level = rec.get_account_level()[0][1]

    @api.depends('balance_date')
    def _balance_start_date(self):
        for rec in self:
            if not rec.balance_date:
                rec.balance_date = date.today()
            if not rec.balance_start_date:
                fy_obj = self.env.user.company_id
                if len(fy_obj) == 0:
                    rec.balance_start_date = date(int(rec.balance_date.year),1,1)
                else:
                    fy_day = self.env.user.company_id.fiscalyear_last_day
                    fy_month = self.env.user.company_id.fiscalyear_last_month
                    start_of_fy = date(rec.balance_date.year, (fy_month), (fy_day))
                    start_of_fy = start_of_fy + relativedelta(days=1) - relativedelta(years=1)
                    rec.balance_start_date = start_of_fy

    def _balance_type(self):
        for rec in self:
            if not rec.balance_type:
                rec.balance_type = 'posted'

    @api.multi
    def get_balance_on_date(self, balance_start_date=None, balance_date=None, balance_type='posted'):
        # TODO: Remove this function (absolute and not called)
        if balance_date is None:
            balance_date = date.today()
        if balance_start_date is None:
            fy_obj = self.env['res.config.settings'].search([('company_id', '=', self.env.user.company_id.id)]).sorted(key=lambda r: r.id, reverse=True)

            if len(fy_obj) == 0:
                balance_start_date = datetime.strptime('01' + '01' + str(balance_date)[:4], '%m%d%Y').date()
            else:
                fy_day = fy_obj[0].fiscalyear_last_day
                fy_month = fy_obj[0].fiscalyear_last_month
                start_of_fy = datetime.strptime(str(fy_month) + str(fy_day) + str(balance_date)[:4], '%m%d%Y').date()
                start_of_fy = start_of_fy + relativedelta(days=1) - relativedelta(years=1)
                balance_start_date = start_of_fy

        for rec in self:
            rec.balance_start_date = balance_start_date
            rec.balance_date = balance_date
            rec.balance_type = balance_type
            rec.total_credit = rec.get_total_credit()[0][1]
            rec.total_debit = rec.get_total_debit()[0][1]

    def get_account_level(self):
        def get_level(major_account):
            level = 0
            while major_account.parent_id:
                level += 1
                major_account = major_account.parent_id
            return level

        return [(0, get_level(account)) for account in self]


    @api.onchange('parent_id')
    @api.multi
    def onchange_parent(self):
        self.name = self.get_account_code()
        self._code_get_fnc()
        self._name_get_fnc()

    @api.constrains('is_leaf')
    def check_is_leaf(self):
        for account in self:
            number_of_account = account.accounts
            number_of_child = account.child_ids
            if len(number_of_account) >= 1 and self.is_leaf== False:
                raise ValidationError(_('Error !This Major Account has An Accounts Remove it First Or Switch To Other major Account'))
            if len(number_of_child) > 0 and self.is_leaf==True:
                raise ValidationError(_('Error !This Major Account Has Children You Can Not Change To Leaf'))

    @api.model
    def get_account_code(self):
        def is_number(s):
            try:
                float(s)
                return True
            except ValueError:
                return False
        brothers = self.env['account.major'].search(
            [('company_id', '=', self.company_id.id),
             ('parent_id', '=', self.parent_id.id and self.parent_id.id or False),
             ('id', '!=', self.id and self.id or 0)]).sorted(key=lambda r: r.id).mapped('name')
        # brothers = [int(x) for x in brothers]
        code = 1
        code_found = False
        while not code_found:
            cf = False
            for x in brothers:
                if not is_number(x):
                    continue
                else:
                    x = int(x)
                if x == code:
                    cf = True
                    continue
            if cf:
                code += 1
            else:
                code_found = True
        level_obj = self.get_account_level()
        level = 0
        if len(level_obj) > 0:
            level = level_obj[0][1]
        level_config = self.env['res.company'].search([('id', '=', self.company_id.id)])

        current_level_length = level_config.major_account_level_setup.search(
            [('level', '=', level), ('company_id', '=', self.company_id.id)]).code_length
        code = str(code)

        for i in xrange(current_level_length - len(code)):
            code = '0' + code
        return code or '----'
        ##self._code_get_fnc()
        ##self._name_get_fnc()

    name = fields.Char(string="Code", required=False, select=True, default = lambda self: self.get_account_code())
    description = fields.Char(string="Account Name", required=True, select=True)
    # complete_name = fields.Char(compute=_name_get_fnc, string='Account Name')
    complete_name = fields.Char(string='Account Full Name')
    ##complete_code = fields.Char(compute=_code_get_fnc, string='Full Code')
    complete_code = fields.Char(string='Full Code',readonly=True,compute='_code_get_fnc',store=True)

    parent_id = fields.Many2one('account.major', 'Parent Account', select=True, ondelete='restrict',
                                domain=[('is_leaf', '=', False)])
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many('account.major', 'parent_id', string='Child Account')
    sequence = fields.Integer('Sequence', select=True,
                              help='Gives the sequence order when majoring a list of accounts.')
    parent_left = fields.Integer('Left Parent', select=1)
    level = fields.Integer('Level', compute='_get_account_level', )
    parent_right = fields.Integer('Right Parent', select=1)
    company_id = fields.Many2one('res.company', string='Company', domain=lambda self: [('id', 'in', self.env.user.company_ids.ids)])
    is_leaf = fields.Boolean('Is Leaf', default=False)
    accounts = fields.One2many("account.account", "major_account_id", string="Accounts")
    total_credit = fields.Float(string="Total Credit", compute='_total_credit')
    total_debit = fields.Float(string="Total Debit", compute='_total_debit', )
    balance = fields.Float(string="Balance", compute='_balance', )
    notes = fields.Text()
    balance_date = fields.Date(string="Balance as on", compute='_balance_date', readonly=False, required=True)
    balance_start_date = fields.Date(string="Balance From", compute='_balance_start_date', readonly=False,
                                     required=True)
    balance_type = fields.Selection(string="Transaction Status",
                                    selection=[('posted', 'Posted'), ('all', 'All Transactions')],
                                    compute='_balance_type', default='posted', readonly=False, required=True)
    credit_balance = fields.Float(string="Credit Balance", compute='_credit_balance', )
    debit_balance = fields.Float(string="Debit Balance", compute='_debit_balance', )


    _parent_name = 'parent_id'
    _parent_store = True
    _parent_order = 'complete_code'
    _order = 'parent_left'
    _rec_name = 'description'

    _constraints = [
        (models.Model._check_recursion, 'Error ! You cannot create recursive account.', ['parent_id'])
    ]

    @api.multi
    def write(self, vals):
        if 'parent_id' in vals:
            if vals['parent_id']:
                parent_level = \
                    self.env['account.major'].browse(vals['parent_id']).get_account_level()[0][1]
                for account in self:
                    level_config = self.env['res.company'].search([('id', '=', account.company_id.id)])
                    if parent_level + 1 >= level_config.major_accounts_levels:
                        raise UserError(_('Level of this account is greater than the maximum allowed level!!'))
                        return

        super_result = super(AccountMajor, self).write(vals)

        if 'name' in vals or 'parent_id' in vals:
            self.update_accounts_code()

        return super_result

    @api.onchange('parent_id')
    def get_major_account_domain(self):
        company_id = self.env.user.company_id
        return {
            'domain': {'parent_id': [('is_leaf', '=', False), '|', ('company_id', '=', company_id.id), ('company_id', '=', False)]}}

    @api.model
    def create(self, vals):
        if 'parent_id' in vals:
            if vals['parent_id']:
                parent_level = \
                    self.env['account.major'].browse(vals['parent_id']).get_account_level()[0][1]
                level_config = self.env['res.company'].search([('id', '=', self.env.user.company_id.id)])
                if parent_level + 1 >= level_config.major_accounts_levels:
                    raise UserError(_('Level of this account is greater than the maximum allowed level!!'))
                    return
        return super(AccountMajor, self).create(vals)


class AccountLevel(models.Model):
    _name = 'account.major.level'

    name = fields.Char(string='Level Name', required=True, readonly=True)
    level = fields.Integer(string='Level', required=True, readonly=True)
    code_length = fields.Integer(string='Code Length', required=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)


class AccountMajorTemplate(models.Model):
    _name = 'account.major.template'

    @api.multi
    def get_account_level(self):
        def get_level(major_account):
            level = 0
            while major_account.parent_id:
                level += 1
                major_account = major_account.parent_id
            return level

        return get_level(self) 

    @api.multi
    def get_max_level(self):
        account_list = self.env['account.major.template'].search([])
        max_level = 0
        for acc in account_list:
            if acc.get_account_level() > max_level:
                max_level = acc.get_account_level()
        return max_level

    name = fields.Char(string="Code", required=False, select=True)
    description = fields.Char(string="Account Name", required=False, select=True)
    parent_id = fields.Many2one('account.major.template', 'Parent Account', select=True, ondelete='restrict',
                                domain=[('is_leaf', '=', False)])
    child_ids = fields.One2many('account.major.template', 'parent_id', string='Child Account')
    parent_left = fields.Integer('Left Parent', select=1)
    parent_right = fields.Integer('Right Parent', select=1)
    is_leaf = fields.Boolean('Is Leaf', default=False)

