from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    multiple_sku_one_stock = fields.Boolean("Manage Multiple Stock Variant by Flow Heineken", default=False)
    deduct_amount_parent_product = fields.Integer("Deductible amount of parent product when it be sold", default=1)
    display_deduct_parent_product = fields.Boolean(compute='compute_display_deduct_parent_product', default=False,
                                                   store=True)
    variant_manage_stock = fields.Many2one('product.product', domain="[('product_tmpl_id', '=', id)]",
                                           string="Variant Manage Stock")
    # variant_compute = fields.Boolean(default=False)
    origin_qty = fields.Float("Origin Qty", store=True)

    # @api.multi
    # @api.depends('variant_manage_stock')
    # def compute_origin_qty(self):
    #     for rec in self:
    #         rec.origin_qty = rec.variant_manage_stock.quantity

    @api.depends('variant_manage_stock')
    def _compute_product_variant_id(self):
        for p in self:
            if self.multiple_sku_one_stock:
                p.product_variant_id = p.variant_manage_stock.id
            else:
                p.product_variant_id = p.product_variant_ids[:1].id

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
            template.origin_qty = qty_available

            if template.multiple_sku_one_stock:
                for p in template.variant_manage_stock:
                    # print(variants_available[p.id]["qty_available"] * p.deduct_amount_parent_product)
                    qty_available += variants_available[p.id]["qty_available"] * p.deduct_amount_parent_product
                    virtual_available += variants_available[p.id]["virtual_available"] * p.deduct_amount_parent_product
                    incoming_qty += variants_available[p.id]["incoming_qty"] * p.deduct_amount_parent_product
                    outgoing_qty += variants_available[p.id]["outgoing_qty"] * p.deduct_amount_parent_product
                prod_available[template.id] = {
                    "qty_available": qty_available,
                    "virtual_available": virtual_available,
                    "incoming_qty": incoming_qty,
                    "outgoing_qty": outgoing_qty,
                }
            else:
                for p in template.product_variant_ids:
                    qty_available += variants_available[p.id]["qty_available"]
                    virtual_available += variants_available[p.id]["virtual_available"]
                    incoming_qty += variants_available[p.id]["incoming_qty"]
                    outgoing_qty += variants_available[p.id]["outgoing_qty"]
                    prod_available[template.id] = {
                        "qty_available": qty_available,
                        "virtual_available": virtual_available,
                        "incoming_qty": incoming_qty,
                        "outgoing_qty": outgoing_qty,
                    }

            # print(prod_available)
            template.origin_qty = qty_available
        return prod_available

    # def _compute_quantities_dict(self):
    #     # TDE FIXME: why not using directly the function fields ?
    #     variants_available = self.mapped('product_variant_ids')._product_available()
    #     prod_available = {}
    #     for template in self:
    #         qty_available = 0
    #         virtual_available = 0
    #         incoming_qty = 0
    #         outgoing_qty = 0
    #         # for p in template.variant_manage_stock:
    #         qty_available += variants_available[template.variant_manage_stock.id][
    #                              "qty_available"] * template.variant_manage_stock.deduct_amount_parent_product
    #         virtual_available += variants_available[template.variant_manage_stock.id][
    #                                  "virtual_available"] * template.variant_manage_stock.deduct_amount_parent_product
    #         incoming_qty += variants_available[template.variant_manage_stock.id][
    #                             "incoming_qty"] * template.variant_manage_stock.deduct_amount_parent_product
    #         outgoing_qty += variants_available[template.variant_manage_stock.id][
    #                             "outgoing_qty"] * template.variant_manage_stock.deduct_amount_parent_product
    #         prod_available[template.id] = {
    #             "qty_available": qty_available,
    #             "virtual_available": virtual_available,
    #             "incoming_qty": incoming_qty,
    #             "outgoing_qty": outgoing_qty,
    #         }
    #     return prod_available
