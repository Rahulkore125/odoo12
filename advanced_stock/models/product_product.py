from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_round


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def get_default_lst_price(self):
        return self.product_tmpl_id.list_price

    deduct_amount_parent_product = fields.Integer("Deductible amount of parent product when it be sold", default=1)
    display_deduct_parent_product = fields.Boolean(compute='compute_display_deduct_parent_product', default=False,
                                                   store=True)

    # original_qty = fields.Float("Original Qty")

    @api.multi
    @api.depends('multiple_sku_one_stock')
    def compute_display_deduct_parent_product(self):
        for rec in self:
            if rec.multiple_sku_one_stock:
                rec.display_deduct_parent_product = True

    def _compute_quantities_dict(self, lot_id, owner_id, package_id, from_date=False, to_date=False):
        res = super(ProductProduct, self)._compute_quantities_dict(self._context.get('lot_id'),
                                                                   self._context.get('owner_id'),
                                                                   self._context.get('package_id'),
                                                                   self._context.get('from_date'),
                                                                   self._context.get('to_date'))
        # print(res[68])

        dates_in_the_past = False
        # only to_date as to_date will correspond to qty_available
        to_date = fields.Datetime.to_datetime(to_date)
        if to_date and to_date < fields.Datetime.now():
            dates_in_the_past = True
        if not dates_in_the_past:
            template_qty = dict()
            for e in res:
                product = self.env['product.product'].search([('id', '=', e)])
                product_template = self.env['product.template'].search([('id', '=', product.product_tmpl_id.id)])
                if product.product_tmpl_id.id in template_qty and product.product_tmpl_id.multiple_sku_one_stock:
                    template_qty[product.product_tmpl_id.id][e] = res[e]
                    if product.id == product.product_tmpl_id.variant_manage_stock.id and product.product_tmpl_id.multiple_sku_one_stock:
                        template_qty[product.product_tmpl_id.id]['qty'] = product_template.origin_quantity
                elif product.product_tmpl_id.id not in template_qty and product.product_tmpl_id.multiple_sku_one_stock:
                    template_qty[product.product_tmpl_id.id] = dict()
                    template_qty[product.product_tmpl_id.id][e] = res[e]
                    if product.id == product.product_tmpl_id.variant_manage_stock.id and product.product_tmpl_id.multiple_sku_one_stock:
                        template_qty[product.product_tmpl_id.id]['qty'] = product_template.origin_quantity
                # print(template_qty)

                for f in template_qty:
                    template = self.env['product.template'].search([('id', '=', f)])
                    # print(template_qty[f])
                    length_variant = len(template.product_variant_ids) + 1
                    if template.multiple_sku_one_stock:
                        if 'qty' in template_qty[f] and len(template_qty[f]) == length_variant:
                            # if template_qty[f]['qty'] != template.origin_quantity:
                            #     print(123)
                            for g in template_qty[f]:
                                if g != 'qty':
                                    product = self.env['product.product'].search([('id', '=', g)])
                                    if template_qty[f][g]['qty_available'] * product.deduct_amount_parent_product != template_qty[f]['qty']:
                                        res[g][
                                            'qty_available'] = template.origin_quantity / product.deduct_amount_parent_product
                                        res[g][
                                            'virtual_available'] = template.origin_quantity / product.deduct_amount_parent_product

                                        inventory_wizard = self.env['stock.change.product.qty'].create({
                                            'product_id': g,
                                            'new_quantity': template.origin_quantity / product.deduct_amount_parent_product,
                                        })
                                        inventory_wizard.change_product_qty()
                                    else:
                                        pass
                        else:
                            pass
                    else:
                        pass
        return res
