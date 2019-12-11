from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def get_default_lst_price(self):
        return self.product_tmpl_id.list_price

    deduct_amount_parent_product = fields.Integer("Deductible amount of parent product when it be sold", default=1)
    display_deduct_parent_product = fields.Boolean(compute='compute_display_deduct_parent_product', default=False,
                                                   store=True)
    lst_price = fields.Float(
        # 'Sale Price', default=lambda self: self.get_default_lst_price(),

        help="The sale price is managed from the product template. Click on the 'Configure Variants' button to set the extra attribute prices.")

    @api.multi
    @api.depends('multiple_sku_one_stock')
    def compute_display_deduct_parent_product(self):
        for rec in self:
            if rec.multiple_sku_one_stock:
                rec.display_deduct_parent_product = True
