from odoo import models, fields, api


class ProductChangeQuantity(models.TransientModel):
    _inherit = "stock.change.product.qty"

    @api.constrains('new_quantity')
    def check_new_quantity(self):
        if any(wizard.new_quantity < 0 for wizard in self):
            pass


class Inventory(models.Model):
    _inherit = "stock.inventory"

    def _action_done(self):
        self.action_check()
        self.write({'state': 'done'})
        self.post_inventory()
        return True
