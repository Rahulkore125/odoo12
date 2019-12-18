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

    @api.multi
    @api.depends('multiple_sku_one_stock')
    def compute_display_deduct_parent_product(self):
        for rec in self:
            if rec.multiple_sku_one_stock:
                rec.display_deduct_parent_product = True

    def _compute_quantities_dict(self, lot_id, owner_id, package_id, from_date=False, to_date=False):
        res = super(ProductProduct, self)._compute_quantities_dict(lot_id=lot_id, owner_id=owner_id,
                                                                   package_id=package_id, from_date=from_date,
                                                                   to_date=to_date)

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

                for f in template_qty:
                    template = self.env['product.template'].search([('id', '=', f)])
                    length_variant = len(template.product_variant_ids) + 1
                    if template.multiple_sku_one_stock:
                        if 'qty' in template_qty[f] and len(template_qty[f]) == length_variant:
                            print(template_qty[f])
                            flag1 = True
                            decrease = 0
                            for e in template_qty[f]:
                                if e != 'qty':
                                    product = self.env['product.product'].search([('id', '=', e)])
                                    total = template_qty[f][e][
                                                'qty_available'] * product.deduct_amount_parent_product
                                    if total < template_qty[f]['qty']:
                                        decrease += template.origin_quantity - total
                                    elif total > template_qty[f]['qty']:
                                        break
                            print(decrease)
                            print(total)

                            if decrease > 0:
                                new_quantity = template.origin_quantity - decrease
                                for g in template_qty[f]:
                                    if g != 'qty':
                                        product = self.env['product.product'].search([('id', '=', g)])
                                        if template_qty[f][g][
                                            'qty_available'] * product.deduct_amount_parent_product != total:
                                            res[g][
                                                'qty_available'] = new_quantity / product.deduct_amount_parent_product
                                            res[g][
                                                'virtual_available'] = new_quantity / product.deduct_amount_parent_product

                                        inventory_wizard = self.env['stock.change.product.qty'].create({
                                            'product_id': g,
                                            'new_quantity': new_quantity / product.deduct_amount_parent_product,
                                        })
                                        inventory_wizard.change_product_qty()
                                self.env.cr.execute(
                                    """UPDATE product_template SET origin_quantity = %s WHERE id = %s""" % (
                                        new_quantity, f))
                            elif decrease == 0 and total == template_qty[f]['qty']:
                                pass
                            elif decrease == 0 and total > template_qty[f]['qty']:
                                print(123)
                                for g in template_qty[f]:
                                    if g != 'qty':
                                        product = self.env['product.product'].search([('id', '=', g)])
                                        if template_qty[f][g][
                                            'qty_available'] * product.deduct_amount_parent_product != total:
                                            res[g]['qty_available'] = total / product.deduct_amount_parent_product
                                            res[g]['virtual_available'] = total / product.deduct_amount_parent_product

                                        inventory_wizard = self.env['stock.change.product.qty'].create({
                                            'product_id': g,
                                            'new_quantity': total / product.deduct_amount_parent_product,
                                        })
                                        inventory_wizard.change_product_qty()
                                self.env.cr.execute(
                                    """UPDATE product_template SET origin_quantity = %s WHERE id = %s""" % (
                                        total, f))
                    else:
                        pass
        return res
