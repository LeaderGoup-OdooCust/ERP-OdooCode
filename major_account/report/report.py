# -*- coding: utf-8 -*-
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _


class TrailBalance(models.AbstractModel):
    _name = 'report.major_account.report_major_accounts'

    @api.model
    def _get_report_values(self, docids, data=None):
        if 'form' in data:
            # data from wizard
            cr_dr_balance = data['form']['cr_dr_balance']
            to_date = data['form']['date_to']
            from_date = data['form']['date_from']
            balance_type = data['form']['target_move']
            balance_type_name = data['form']['target_move'] == 'posted' and 'Posted' or 'All'
            for_all_accounts = data['form']['all_accounts']
            selected_major_account = data['form']['selected_account']
            show_detail = data['form']['show_detail']
            report_level = int(data['form']['report_level'])

        else:
            # data not from wizard
            cr_dr_balance = False
            for_all_accounts = True
            selected_major_account = False
            show_detail = False
            report_level = self.env['res.company'].search(
                [('id', '=', self.env.user.company_id.id)]).major_accounts_levels
            balance_type = 'posted'
            balance_type_name = 'Posted'
            to_date = date.today()
            fy_obj = self.env['res.config.settings'].search([('company_id', '=', self.env.user.company_id.id)]).sorted(key=lambda r: r.id, reverse=True)
            if len(fy_obj) == 0:
                from_date = datetime.strptime('01' + '01' + str(to_date)[:4], '%m%d%Y').date()
            else:
                fy_day = fy_obj[0].fiscalyear_last_day
                fy_month = fy_obj[0].fiscalyear_last_month
                start_of_fy = datetime.strptime(str(fy_month) + str(fy_day) + str(to_date)[:4], '%m%d%Y').date()
                start_of_fy = start_of_fy + relativedelta(days=1) - relativedelta(years=1)
                from_date = start_of_fy
        report = self.env['ir.actions.report']._get_report_from_name('major_account.report_major_accounts')
        if not for_all_accounts:
            all_major_accounts = self.env['account.major'].search(
                [('id', 'child_of', selected_major_account)])
        else:
            all_major_accounts = self.env['account.major'].search(
                ['|', ('company_id', 'child_of', self.env.user.company_id.id), ('company_id', '=', False)])

        if not show_detail:
            all_major_accounts = all_major_accounts.filtered(lambda record: record.level < report_level)

        all_major_accounts.get_balance_on_date(from_date, to_date, balance_type)

        cr_total = 0.0
        dr_total = 0.0
        cr_balance = 0.0
        dr_balance = 0.0
        last_counted_account = '!-@'
        for ac in all_major_accounts:
            if ac.accounts:
                pass
                # ac.accounts.compute_balance(to_date, balance_type)
            if not last_counted_account in ac.complete_code:
                cr_total = cr_total + ac.total_credit
                dr_total = dr_total + ac.total_debit
                cr_balance = cr_balance + ac.credit_balance
                dr_balance = dr_balance + ac.debit_balance
                last_counted_account = ac.complete_code
            elif ac.complete_code.index(last_counted_account) != 0:
                cr_total = cr_total + ac.total_credit
                dr_total = dr_total + ac.total_debit
                cr_balance = cr_balance + ac.credit_balance
                dr_balance = dr_balance + ac.debit_balance
                last_counted_account = ac.complete_code

        selected_major_account_object = self.env['account.major'].browse(selected_major_account)

        selected_major_account_name = "All Accounts" if for_all_accounts else \
            selected_major_account_object.complete_code + " " + selected_major_account_object.description

        doc_args = {
            'doc_ids': all_major_accounts._ids,
            'doc_model': report.model,
            'company': self.env.user.company_id.name,
            'balance_start_date': from_date,
            'balance_date': to_date,
            'type': balance_type_name,
            'docs': all_major_accounts.sorted(lambda x: x.complete_code),
            'disp_acc_name': selected_major_account_name,
            'cr_dr_balance': cr_dr_balance,
            'cr_total': cr_total,
            'dr_total': dr_total,
            'cr_balance': cr_balance,
            'dr_balance': dr_balance,
            'level_name': "Detail Level" if show_detail else "Level-" + str(report_level),
            'show_detail': show_detail
        }
        return doc_args
