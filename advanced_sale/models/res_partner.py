from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    title_gender = fields.Selection(string="Title", selection=[('miss', 'Miss'), ('mister', 'Mister')])

