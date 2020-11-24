# -*- coding: utf-8 -*-
{
    'name': "Major Accounts",
    'summary': """
        Major accounts to group chart of account""",
    'description': """
        Major and show the accumulative balances of sub-accounts
    """,

    'author': "M.A.R",
    'website': "http://www.itgroup.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Account Charts',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'om_account_accountant'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/account_res_config_view.xml',
        'views/account_view.xml',
        'security/ir_rule.xml',
        'views/major_account_report.xml',
        'views/report_major_accounts_template.xml',
        'views/report_opening_balance.xml',
        'views/accounts_hierarchy_data.xml',
        'wizard/pdf_report_view.xml',
        # 'views/load_major_account_template_data.yml',
    ],
    # only loaded in demonstration mode
    'demo': [],
}