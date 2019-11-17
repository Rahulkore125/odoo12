from odoo import models, fields


class ProductProduct(models.Model):
    _inherit = 'product.template'

    def _get_default_uom_sale_id(self):
        return self.env["uom.uom"].search([], limit=1, order='id').id

    uom_so_id = fields.Many2one(
        'uom.uom', 'Sale Unit of Measure', required=True, default=_get_default_uom_sale_id,
        help="Default unit of measure used for sale orders")
