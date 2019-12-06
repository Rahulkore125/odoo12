# -*- coding: utf-8 -*-

from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    currency_id = fields.Many2one('res.currency', readonly=True,
                                  default=lambda self: self.env.user.company_id.currency_id)

    def auto_install(self):
        # self.env['res.partner'].search([('create_date', '=', False)]).unlink()
        pass
