from odoo import models, fields, api,tools,_


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
