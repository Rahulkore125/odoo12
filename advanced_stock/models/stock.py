from odoo import models, fields, api, tools, _
from odoo.tools import float_utils, float_compare


class ProductChangeQuantity(models.TransientModel):
    _inherit = "stock.change.product.qty"

    @api.constrains('new_quantity')
    def check_new_quantity(self):
        if any(wizard.new_quantity < 0 for wizard in self):
            pass

    def change_product_qty(self):
        """ Changes the Product Quantity by making a Physical Inventory. """
        Inventory = self.env['stock.inventory']
        for wizard in self:
            product = wizard.product_id.with_context(location=wizard.location_id.id)
            line_data = wizard._action_start_line()
            print(line_data)
            if wizard.product_id.id:
                inventory_filter = 'product'
            else:
                inventory_filter = 'none'
            inventory = Inventory.create({
                'name': _('INV: %s') % tools.ustr(wizard.product_id.display_name),
                'filter': inventory_filter,
                'product_id': wizard.product_id.id,
                'location_id': wizard.location_id.id,
                'line_ids': [(0, 0, line_data)],
            })
            inventory.action_validate()
        product = self.env['product.product'].search([('id', '=', line_data['product_id'])])
        if product.product_tmpl_id.multiple_sku_one_stock:
            product.product_tmpl_id.origin_quantity = line_data['product_qty']
        return {'type': 'ir.actions.act_window_close'}


class Inventory(models.Model):
    _inherit = "stock.inventory"

    def _action_done(self):
        self.action_check()
        self.write({'state': 'done'})
        self.post_inventory()
        return True

    def action_validate(self):
        inventory_lines = self.line_ids.filtered(lambda l: l.product_id.tracking in ['lot',
                                                                                     'serial'] and not l.prod_lot_id and l.theoretical_qty != l.product_qty)
        print(inventory_lines)
        lines = self.line_ids.filtered(lambda l: float_compare(l.product_qty, 1,
                                                               precision_rounding=l.product_uom_id.rounding) > 0 and l.product_id.tracking == 'serial' and l.prod_lot_id)
        print(lines)
        if inventory_lines and not lines:
            wiz_lines = [(0, 0, {'product_id': product.id, 'tracking': product.tracking}) for product in
                         inventory_lines.mapped('product_id')]
            wiz = self.env['stock.track.confirmation'].create({'inventory_id': self.id, 'tracking_line_ids': wiz_lines})
            return {
                'name': _('Tracked Products in Inventory Adjustment'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'stock.track.confirmation',
                'target': 'new',
                'res_id': wiz.id,
            }
        else:
            self._action_done()

    def action_check(self):
        """ Checks the inventory and computes the stock move to do """
        # tde todo: clean after _generate_moves
        for inventory in self.filtered(lambda x: x.state not in ('done', 'cancel')):
            # first remove the existing stock moves linked to this inventory
            inventory.mapped('move_ids').unlink()
            inventory.line_ids._generate_moves()
            print(inventory.line_ids)
            for e in inventory.line_ids:
                if e.product_id.product_tmpl_id.multiple_sku_one_stock:
                    print(e.product_id.product_tmpl_id.variant_manage_stock.id)

                    if e.product_id.id == e.product_id.product_tmpl_id.variant_manage_stock.id:
                        e.product_id.product_tmpl_id.origin_quantity = e.product_qty


class InventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    def _generate_moves(self):
        vals_list = []
        for line in self:

            if float_utils.float_compare(line.theoretical_qty, line.product_qty,
                                         precision_rounding=line.product_id.uom_id.rounding) == 0:
                continue
            diff = line.theoretical_qty - line.product_qty
            if diff < 0:  # found more than expected
                vals = line._get_move_values(abs(diff), line.product_id.property_stock_inventory.id,
                                             line.location_id.id, False)
            else:
                vals = line._get_move_values(abs(diff), line.location_id.id,
                                             line.product_id.property_stock_inventory.id, True)
            vals_list.append(vals)
        return self.env['stock.move'].create(vals_list)
