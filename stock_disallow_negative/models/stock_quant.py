
from odoo import models, api, _
from odoo.exceptions import ValidationError
from odoo.tools import config, float_compare


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.multi
    @api.constrains('product_id', 'quantity')
    def check_negative_qty(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for quant in self:
            if (
                float_compare(quant.quantity, 0, precision_digits=precision) == -1 and
                quant.product_id.type == 'product' and
                quant.location_id.usage in ['internal', 'transit']
            ):
                raise ValidationError(_(
                    "You cannot validate this stock operation because the "
                    "stock level of the product '%s' would become negative "
                    "(%s) on the stock location '%s' and negative stock is "
                    "not allowed.") % (
                        quant.product_id.display_name, quant.quantity,
                        quant.location_id.complete_name))
