from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    deduct_amount_parent_product = fields.Integer("Deductible amount of parent product when it be sold", default=1)
    display_deduct_parent_product = fields.Boolean(_compute='_compute_display_deduct_parent_product', default=False)

    @api.multi
    @api.depends('product_tmpl_id')
    def _compute_display_deduct_parent_product(self):
        for rec in self:
            if rec.product_tmpl_id.multiple_sku_one_stock:
                rec.display_deduct_parent_product = True