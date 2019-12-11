from odoo import models, fields,api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # def get_default_lst_price(self):
    #     return self.list_price

    multiple_sku_one_stock = fields.Boolean("Manage Multiple Stock Variant by Flow Heineken",default=False)
    deduct_amount_parent_product = fields.Integer("Deductible amount of parent product when it be sold", default=1)
    display_deduct_parent_product = fields.Boolean(compute='compute_display_deduct_parent_product', default=False,
                                                   store=True)

    # lst_price = fields.Float(
    #     'Public Price', readonly=False,
    #     digits=dp.get_precision('Product Price'), default= lambda self: self.get_default_lst_price())

    @api.multi
    @api.depends('multiple_sku_one_stock')
    def compute_display_deduct_parent_product(self):
        for rec in self:
            if rec.multiple_sku_one_stock:
                rec.display_deduct_parent_product = True

    def _compute_quantities_dict(self):
        # TDE FIXME: why not using directly the function fields ?
        variants_available = self.mapped('product_variant_ids')._product_available()
        prod_available = {}
        for template in self:
            qty_available = 0
            virtual_available = 0
            incoming_qty = 0
            outgoing_qty = 0
            for p in template.product_variant_ids:
                qty_available += variants_available[p.id]["qty_available"]*p.deduct_amount_parent_product
                virtual_available += variants_available[p.id]["virtual_available"]*p.deduct_amount_parent_product
                incoming_qty += variants_available[p.id]["incoming_qty"]*p.deduct_amount_parent_product
                outgoing_qty += variants_available[p.id]["outgoing_qty"]*p.deduct_amount_parent_product
            prod_available[template.id] = {
                "qty_available": qty_available,
                "virtual_available": virtual_available,
                "incoming_qty": incoming_qty,
                "outgoing_qty": outgoing_qty,
            }
        return prod_available