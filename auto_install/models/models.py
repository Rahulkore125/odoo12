# -*- coding: utf-8 -*-

from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def auto_install(self):
        self.env.cr.execute("DELETE FROM account_invoice")
        self.env.cr.execute("DELETE FROM account_invoice_line");
        self.env.cr.execute("DELETE FROM account_invoice_line");
        self.env.cr.execute("DELETE FROM stock_change_product_qty");

        self.env.cr.execute("DELETE FROM sale_order")
        self.env.cr.execute("DELETE from account_payment")
        self.env.cr.execute("DELETE from magento_pull_history WHERE name = 'sale_orders'")
        self.env.cr.execute("DELETE from account_partial_reconcile")
        self.env.cr.execute("DELETE from account_move")
        self.env.cr.execute("DELETE from account_move_line")
        self.env.cr.execute("DELETE from stock_inventory")
        self.env.cr.execute("DELETE from stock_picking")
        self.env.cr.execute("DELETE from stock_return_picking")
        self.env.cr.execute("DELETE from stock_move")
        self.env.cr.execute("DELETE from stock_quant")
        self.env.cr.execute("DELETE  from product_template WHERE is_magento_product = True")
        self.env.cr.execute("DELETE from magento_pull_history WHERE name = 'normal_product'")
        self.env.cr.execute("DELETE from magento_pull_history WHERE name = 'categories'")
        self.env.cr.execute("DELETE from magento_product_attribute")
        self.env.cr.execute("DELETE from magento_product_category")









        # self.env.cr.execute("UPDATE magento_product_product SET odoo_id = 68 WHERE external_id = 240")
        # self.env.cr.execute("UPDATE magento_product_product SET odoo_id = 69 WHERE external_id = 255")

        self.env.cr.execute("UPDATE magento_backend SET auto_fetching = FALSE ")


