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
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations()
        domain_quant = [('product_id', 'in', self.ids)] + domain_quant_loc
        dates_in_the_past = False
        # only to_date as to_date will correspond to qty_available
        to_date = fields.Datetime.to_datetime(to_date)
        if to_date and to_date < fields.Datetime.now():
            dates_in_the_past = True

        domain_move_in = [('product_id', 'in', self.ids)] + domain_move_in_loc
        domain_move_out = [('product_id', 'in', self.ids)] + domain_move_out_loc
        if lot_id is not None:
            domain_quant += [('lot_id', '=', lot_id)]
        if owner_id is not None:
            domain_quant += [('owner_id', '=', owner_id)]
            domain_move_in += [('restrict_partner_id', '=', owner_id)]
            domain_move_out += [('restrict_partner_id', '=', owner_id)]
        if package_id is not None:
            domain_quant += [('package_id', '=', package_id)]
        if dates_in_the_past:
            domain_move_in_done = list(domain_move_in)
            domain_move_out_done = list(domain_move_out)
        if from_date:
            domain_move_in += [('date', '>=', from_date)]
            domain_move_out += [('date', '>=', from_date)]
        if to_date:
            domain_move_in += [('date', '<=', to_date)]
            domain_move_out += [('date', '<=', to_date)]

        Move = self.env['stock.move']
        Quant = self.env['stock.quant']
        domain_move_in_todo = [('state', 'in',
                                ('waiting', 'confirmed', 'assigned', 'partially_available'))] + domain_move_in
        domain_move_out_todo = [('state', 'in',
                                 ('waiting', 'confirmed', 'assigned', 'partially_available'))] + domain_move_out
        moves_in_res = dict((item['product_id'][0], item['product_qty']) for item in
                            Move.read_group(domain_move_in_todo, ['product_id', 'product_qty'], ['product_id'],
                                            orderby='id'))
        moves_out_res = dict((item['product_id'][0], item['product_qty']) for item in
                             Move.read_group(domain_move_out_todo, ['product_id', 'product_qty'], ['product_id'],
                                             orderby='id'))
        quants_res = dict((item['product_id'][0], item['quantity']) for item in
                          Quant.read_group(domain_quant, ['product_id', 'quantity'], ['product_id'], orderby='id'))
        if dates_in_the_past:
            # Calculate the moves that were done before now to calculate back in time (as most questions will be recent ones)
            domain_move_in_done = [('state', '=', 'done'), ('date', '>', to_date)] + domain_move_in_done
            domain_move_out_done = [('state', '=', 'done'), ('date', '>', to_date)] + domain_move_out_done
            moves_in_res_past = dict((item['product_id'][0], item['product_qty']) for item in
                                     Move.read_group(domain_move_in_done, ['product_id', 'product_qty'], ['product_id'],
                                                     orderby='id'))
            moves_out_res_past = dict((item['product_id'][0], item['product_qty']) for item in
                                      Move.read_group(domain_move_out_done, ['product_id', 'product_qty'],
                                                      ['product_id'], orderby='id'))

        res = dict()
        for product in self.with_context(prefetch_fields=False):
            # if product.product_tmpl_id.multiple_sku_one_stock:
            #     template_available = product.product_tmpl_id._compute_quantities_dict()
            #     res[product.id]['qty_available'] = template_available['qty_available']
            #     res[product.id]['incoming_qty'] = template_available['incoming_qty']
            #     res[product.id]['virtual_available'] = template_available['virtual_available']
            #     res[product.id]['outgoing_qty'] = template_available['outgoing_qty']
            # else:
            product_id = product.id
            rounding = product.uom_id.rounding
            res[product_id] = {}
            if dates_in_the_past:
                qty_available = quants_res.get(product_id, 0.0) - moves_in_res_past.get(product_id,
                                                                                        0.0) + moves_out_res_past.get(
                    product_id, 0.0)
            else:
                qty_available = quants_res.get(product_id, 0.0)
            res[product_id]['qty_available'] = float_round(qty_available, precision_rounding=rounding)
            res[product_id]['incoming_qty'] = float_round(moves_in_res.get(product_id, 0.0),
                                                          precision_rounding=rounding)
            res[product_id]['outgoing_qty'] = float_round(moves_out_res.get(product_id, 0.0),
                                                          precision_rounding=rounding)
            res[product_id]['virtual_available'] = float_round(
                qty_available + res[product_id]['incoming_qty'] - res[product_id]['outgoing_qty'],
                precision_rounding=rounding)

        template_qty = dict()

        for e in res:
            product = self.env['product.product'].search([('id', '=', e)])
            if product.product_tmpl_id.id in template_qty:
                template_qty[product.product_tmpl_id.id][e] = res[e]
                if product.id == product.product_tmpl_id.variant_manage_stock.id:
                    template_qty[product.product_tmpl_id.id]['qty'] = res[e][
                                                                          'qty_available'] * product.deduct_amount_parent_product
            else:
                template_qty[product.product_tmpl_id.id] = dict()
                template_qty[product.product_tmpl_id.id][e] = res[e]
                if product.id == product.product_tmpl_id.variant_manage_stock.id:
                    template_qty[product.product_tmpl_id.id]['qty'] = res[e][
                                                                          'qty_available'] * product.deduct_amount_parent_product


        print(template_qty)

        # for f in template_qty:
        #     template = self.env['product.template'].search([('id', '=', f)])
        #     if template.multiple_sku_one_stock:
        #         flag1 = True
        #         for e in template_qty[f]:
        #             product = self.env['product.product'].search([('id', '=', e)])
        #             total = template_qty[f][e]['qty_available'] * product.deduct_amount_parent_product
        #             # print(template.qty_available)
        #             if total != template.qty_available:
        #                 flag1 = False
        #                 break
        #         # flag2 = True
        #         # for e in template_qty[f]:
        #         # print(template.qty_available)
        #         if not flag1:
        #             # print(flag)
        #             for e in template_qty[f]:
        #                 # print(total)
        #                 product = self.env['product.product'].search([('id', '=', e)])
        #                 print(product.qty_available * product.deduct_amount_parent_product)
        #                 # print(template.qty_available)
        #                 if product.qty_available * product.deduct_amount_parent_product == template.qty_available:
        #                     res[e]['qty_available'] = total / product.deduct_amount_parent_product
        #                 # self.env['stock.quant'].search([('product_id', '=', e), ('location_id', '=', 12)]).update({
        #                 #     'quantity':  total / product.deduct_amount_parent_product
        #                 # })
        #                     inventory_wizard = self.env['stock.change.product.qty'].create({
        #                         'product_id': e,
        #                         'new_quantity': total/product.deduct_amount_parent_product,
        #                     })
        #                     inventory_wizard.change_product_qty()
        # print(template_qty[f])
        # print(res)
        return res
