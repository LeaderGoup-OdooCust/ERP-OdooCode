# -*- coding: utf-8 -*-
from odoo.tests import common

class TestAccountMajorCommon(common.TransactionCase):

    post_install = True

    def setUp(self):
        super(TestAccountMajorCommon, self).setUp()

        self.account1 = self.env['account.major'].create({'description':'profit and lost'})
        self.account2 = self.env['account.major'].create({'description':'income','parent_id':self.account1.id,'is_leaf':True})
        self.account3= self.env['account.major'].create({'description':'coust','parent_id':self.account1.id,'is_leaf':True})
        self.account_name1 = self.env['account.account'].create({'code':'101012','name':'fixed assest','user_type_id':3 ,'major_account_id':self.account2.id})
        self.account_name2 = self.env['account.account'].create({'code':'101013','name':'pay','user_type_id':3 ,'major_account_id':self.account2.id})
        self.account_name3 = self.env['account.account'].create({'code':'101014','name':'receve','user_type_id':3,'major_account_id': self.account3.id})



