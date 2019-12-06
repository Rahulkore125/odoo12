# -*- coding: utf-8 -*-

from odoo import models,fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    currency_id = fields.Many2one('res.currency', readonly=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    def auto_install(self):
        self.env.cr.execute("UPDATE ir_module_module SET state = 'installed' WHERE name = 'magento2_connector'")
        self.env.cr.execute("UPDATE ir_module_module SET state = 'installed' WHERE name = 'advanced_sale'")

