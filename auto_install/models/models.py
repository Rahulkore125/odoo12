# -*- coding: utf-8 -*-

from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def auto_install(self):
        self.env.cr.execute("DELETE FROM account_invoice")
        self.env.cr.execute("DELETE FROM sale_order")
        self.env.cr.execute("DELETE from account_payment")
        self.env.cr.execute("DELETE from magento_pull_history WHERE name = 'sale_orders'")
        self.env.cr.execute("DELETE from account_partial_reconcile")
        self.env.cr.execute("DELETE from account_move")
        self.env.cr.execute("DELETE from account_move_line")

