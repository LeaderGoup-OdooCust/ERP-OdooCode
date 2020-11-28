# -*- coding: utf-8 -*-
{
    'name': "Accounting Cheque Management",

    'summary': """
Inbound and outbound cheque module""",

    'description': """
Inbound & Outbound Cheques
====================
The specific and easy-to-use Cheques system in Odoo allows you to keep track of your accounting, even when you are not an accountant. It provides an easy way to follow up on your vendors and customers cheques.

You could use this simplified accounting in case you work with an (external) account to keep your books, and you still want to keep track of cheque payments. This module also offers you an easy method of registering cheque payments, without having to encode complete abstracts of account.
    """,

    'author': "Mohamed Mahmoud Amin",
    'website': "http://www.yourcompany.com",

    'category': 'Invoicing Management',

    'version': '0.1',

    'depends': ['account'],

    'data': [
        'security/ir.model.access.csv',
        'data/account_journal_data.xml',
        'data/sequence.xml',
        'wizard/printing_cheque_wiz_view.xml',
        'wizard/cheque_wiz_view.xml',
        'views/account_cheque_view.xml',
        'views/res_bank_view.xml',
        'views/account_journal_view.xml',
        'views/account_payment_view.xml',
        'views/cheque_user_template_view.xml',
        'report/printing_cheque_report.xml',
    ],

    'external_dependencies': {'python3': ['num2words']},

}