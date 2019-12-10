from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # deduct_amount_parent_product = fields.Integer("Deductible amount of parent product when it be sold", default=1)
    # display_deduct_parent_product = fields.Boolean(compute='compute_display_deduct_parent_product', default=False,store=True)
    #
    # @api.multi
    # @api.depends('multiple_sku_one_stock')
    # def compute_display_deduct_parent_product(self):
    #     for rec in self:
    #         if rec.multiple_sku_one_stock:
    #             rec.display_deduct_parent_product = True