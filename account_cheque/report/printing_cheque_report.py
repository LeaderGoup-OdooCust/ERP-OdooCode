from odoo import models, fields, api

class PrintingChequeReport(models.AbstractModel):
    _name = 'report.account_cheque.printing_cheque_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        docargs = {}
        report = self.env['ir.actions.report']._get_report_from_name('account_cheque.printing_cheque_template')
        if data:
            docargs['doc_ids'] = self.ids
            docargs['doc_model'] = report.model
            docargs['data'] = data
        return docargs
