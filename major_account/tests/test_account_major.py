# -*- coding: utf-8 -*-

from .test_account_major_common import TestAccountMajorCommon
from datetime import datetime,date


class TestAccountisplay(TestAccountMajorCommon):

    def test_totalDebit(self):
        today = datetime.today()
        account_id1= self.account_name1
        account_id2 = self.account_name2
        # account_id3 =   self.account_name3
        account_move = self.env['account.move']
        journal=self.env['account.journal'].search([('name', '=', 'Miscellaneous Operations')])
        debit_val={
            'account_id':account_id1.id,
            'debit':5,
            'credit': 0.0,
            'name': '/',
            'date_maturity': today,
         }

        credit_val={
            'account_id': account_id2.id,
            'debit': 0.0,
            'credit':5,
            'name': '/',
            'date_maturity': today,
        }

        move_id=account_move.create({
            'journal_id':journal.id,
            'date':today,
            'state':'posted',
            'line_ids':[(0, 0,debit_val),(0, 0,credit_val)]
        })

        total_debit = self.account2.get_total_debit()[0][1]
        self.assertEqual(total_debit, 5)


    def test_totalCredit(self):
        today = datetime.today()
        account_id2 = self.account_name2
        account_id3 =   self.account_name3
        account_move = self.env['account.move']
        journal = self.env['account.journal'].search([('name', '=', 'Miscellaneous Operations')])
        debit_val = {
            'account_id': account_id2.id,
            'debit': 100,
            'credit': 0.0,
            'name': '/',
            'date_maturity': today,
        }

        credit_val = {
            'account_id': account_id3.id,
            'debit': 0.0,
            'credit': 100,
            'name': '/',
            'date_maturity': today,
        }

        move_id = account_move.create({
            'journal_id': journal.id,
            'date': today,
            'state': 'posted',
            'line_ids': [(0, 0, debit_val), (0, 0, credit_val)]
        })
        total_credit= self.account3.get_total_credit()[0][1]
        self.assertEqual(total_credit, 100)
    def test_Balance(self):
        balance_type = "posted"
        balance_date = date.today()
        balance_start_date = datetime.strptime('01' + '01' + '2017', '%m%d%Y').date()
        today = datetime.today()
        account_id2 = self.account_name2
        account_id3 = self.account_name3
        account_move = self.env['account.move']

        journal = self.env['account.journal'].search([('name', '=', 'Miscellaneous Operations')])
        debit_val = {
            'account_id': account_id2.id,
            'debit': 200,
            'credit': 0.0,
            'name': '/',
            'date_maturity': today,
        }

        credit_val = {
            'account_id': account_id3.id,
            'debit': 0.0,
            'credit': 200,
            'name': '/',
            'date_maturity': today,
        }

        move_id = account_move.create({
            'journal_id': journal.id,
            'date': today,
            'state': 'posted',
            'line_ids': [(0, 0, debit_val), (0, 0, credit_val)]
        })
        self.account2._balance()
        balance= self.account2.balance

        self.assertEqual(balance, 200)

        
    
    def test_getName(self):
        major_account=self.account2
        major_name=major_account.name_get()
        self.assertEqual(str(major_name[0][1]),'YourCompany/1/1 income')



    def test_code(self):
        major_account = self.account1
        major_name = major_account.code_get()
        self.assertEqual(str(major_name[0][1]),'YourCompany/1')




        
        
        
        
        
    
    




















