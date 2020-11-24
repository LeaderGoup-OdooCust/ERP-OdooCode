from odoo import fields, models,_
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class AccountStatementReport(models.TransientModel):
    _inherit = "account.common.account.report"
    _name = 'major_account.report'
    _description = 'Trail Balance Account Major Report'

    def _level_to_select(self):
        list_of_levels = []
        max_level = self.env['res.company'].search(
            [('id', '=', self.env.user.company_id.id)]).major_accounts_levels
        for x in range(1, max_level + 1):
            list_of_levels.append((str(x), str(x)))
        return list_of_levels

    def _get_start_year(self):
        fy_obj = self.env['res.config.settings'].search([('company_id', '=', self.env.user.company_id.id)]).sorted(key=lambda r: r.id, reverse=True)

        if len(fy_obj) == 0:
            year_start_date = datetime.strptime('01' + '01' + str(datetime.today())[:4], '%m%d%Y').date()
        else:
            fy_day = self.env.user.company_id.fiscalyear_last_day
            fy_month = self.env.user.company_id.fiscalyear_last_month
            start_of_fy = datetime.strptime(str(fy_month) + str(fy_day) + str(datetime.today())[:4], '%m%d%Y').date()
            start_of_fy = start_of_fy + relativedelta(days=1) - relativedelta(years=1)
            year_start_date = start_of_fy
        return year_start_date

    date_from = fields.Date(required=True, default=lambda self: self._get_start_year())
    date_to = fields.Date(required=True, default=fields.Date.today)
    all_accounts = fields.Boolean(string="All Major Accounts", default=True)
    cr_dr_balance = fields.Boolean('Credit/Debit Balance',default=False)
    show_cr_de_opening_balance = fields.Boolean("Show Credit/Debuit Opening Balance" , default=False)
    selected_account = fields.Many2one('account.major', string="Major Account")
    report_level = fields.Selection(selection='_level_to_select', string="Up To Level", required=True,
                                    default=lambda self: str(self.env['res.company'].search(
                                        [('id', '=', self.env.user.company_id.id)]).major_accounts_levels))
    show_detail = fields.Boolean(string="Show Detailed Accounts", default=False)

    def _print_report(self, data):
        data['form']['all_accounts'] = self.all_accounts
        data['form']['selected_account'] = self.selected_account.id
        data['form']['report_level'] = self.report_level
        data['form']['show_detail'] = self.show_detail
        data['form']['cr_dr_balance'] = self.cr_dr_balance
        data['form']['show_cr_de_opening_balance'] = self.show_cr_de_opening_balance

        if not self.all_accounts and not self.show_detail:
            if self.selected_account.level > int(self.report_level) -1:
                raise UserError("The selected reporting level is less than level of selected account")
        data = self.pre_print_report(data)
        if self.show_cr_de_opening_balance and self.cr_dr_balance:
            return self.env.ref('major_account.action_report_major_account_open_balance').report_action(self, data=data)
        else:
            return self.env.ref('major_account.action_report_major_account').report_action(self, data=data)

