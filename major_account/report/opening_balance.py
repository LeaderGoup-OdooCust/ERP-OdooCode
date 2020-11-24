from datetime import datetime, timedelta

from odoo import models, fields, api, _


class TrailBalance(models.AbstractModel):
    _name = 'report.major_account.report_show_opening_balance'

    @api.multi
    def _get_open_balance(self, account, to_date):
        """ opening balance for account """
        open_balance_date = datetime.strptime(to_date, fields.DATE_FORMAT) + timedelta(days=-1)
        account.get_balance_on_date(balance_date=open_balance_date)
        balance = account.total_debit - account.total_credit
        return balance

    # method  to get  total debit
    def get_total_debit(self, account, from_date, to_date):
        #TODO: change method from being
        for rec in account:
            total_debit = 0
            balance_type = 'posted'
            if rec.is_leaf:
                for account in rec.accounts:
                    total_debit += account.get_debit_on_period(from_date, to_date, balance_type)
            else:
                if rec.child_ids:
                    for child_account in rec.child_ids:
                        total_debit += self.get_total_debit(child_account, from_date, to_date)
        return total_debit

    def get_total_credit(self, account, from_date, to_date):
        for rec in account:
            total_credit = 0
            balance_type = 'posted'

            if rec.is_leaf:
                for account in rec.accounts:
                    total_credit += account.get_credit_on_period(from_date, to_date, balance_type)
            else:
                if rec.child_ids:
                    for child_account in rec.child_ids:
                        total_credit += self.get_total_credit(child_account, from_date, to_date)
        return total_credit

    def get_balance(self, account, to_date):
        date = datetime.strptime(to_date, fields.DATE_FORMAT)
        account.get_balance_on_date(balance_date=date)
        balance = account.total_debit - account.total_credit
        return balance

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        if 'form' in data:
            cr_dr_balance = data['form']['cr_dr_balance']
            to_date = data['form']['date_to']
            from_date = data['form']['date_from']
            for_all_accounts = data['form']['all_accounts']
            selected_major_account = data['form']['selected_account']
            show_detail = data['form']['show_detail']
            report_level = int(data['form']['report_level'])

        if not for_all_accounts:
            all_major_accounts = self.env['account.major'].search(
                [('id', 'child_of', selected_major_account)])
        else:
            all_major_accounts = self.env['account.major'].search(
                [('company_id', '=', self.env.user.company_id.id)])
        if not show_detail:
            all_major_accounts = all_major_accounts.filtered(lambda record: record.level < report_level)
        self.model = self.env.context.get('active_model')
        selected_major_account_object = self.env['account.major'].browse(selected_major_account)
        selected_major_account_name = "All Accounts" if for_all_accounts else \
            selected_major_account_object.complete_code + " " + selected_major_account_object.description
        doc_args = {
            'doc_ids':self.ids,
            'doc_model': self.model,
            'company': self.env.user.company_id.name,
            'data': data['form'],
            'level_name': "Detail Level" if show_detail else "Level-" + str(report_level),
            'disp_acc_name': selected_major_account_name,
            'balance_start_date': from_date,
            'get_open_balance': self._get_open_balance,
            'get_total_credit':self.get_total_credit,
            'get_total_debit':self.get_total_debit,
            'get_balance':self.get_balance,
            'balance_date': to_date,
            'docs': all_major_accounts,
            'cr_dr_balance': cr_dr_balance,
            'level_name': "Detail Level" if show_detail else "Level-" + str(report_level),
            'show_detail': show_detail
        }
        return report_obj.render('major_account.report_show_opening_balance', doc_args)

