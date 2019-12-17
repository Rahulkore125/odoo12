from datetime import date

from odoo import fields, models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    date_done_delivery = fields.Date()
    is_return_picking = fields.Boolean(default=False)
    has_return_picking = fields.Boolean(default=False)
    date_return = fields.Date()


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def create_returns(self):
        for wizard in self:
            new_picking_id, pick_type_id = super(StockReturnPicking, wizard)._create_returns()
            # Override the context to disable all the potential filters that could have been set previously
        ctx = dict(self.env.context)

        ctx.update({
            'search_default_picking_type_id': pick_type_id,
            'search_default_draft': False,
            'search_default_assigned': False,
            'search_default_confirmed': False,
            'search_default_ready': False,
            'search_default_late': False,
            'search_default_available': False,
        })

        picking = self.env['stock.picking'].search([('id', '=', new_picking_id)])
        for move_line in picking.move_lines:
            move_line.quantity_done = move_line.product_uom_qty
        picking.action_done()
        picking.is_return_picking = True

        picking.date_return = date.today()
        origin_picking = self.env['stock.picking'].search(
            [('sale_id', '=', picking.sale_id.id), ('is_return_picking', '=', False)])
        origin_picking.has_return_picking = True
        action = self.env['sale.order'].browse(picking.sale_id.id).action_view_delivery()

        return action


class StockMove(models.Model):
    _inherit = "stock.move"

    to_refund = fields.Boolean(string="To Refund (update SO/PO)", copy=False,
                               help='Trigger a decrease of the delivered/received quantity in the associated Sale Order/Purchase Order',
                               default=True)


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    def _get_scrap_uom(self):
        unit_measure = self.env.ref('uom.product_uom_unit').id
        return unit_measure

    product_uom_id = fields.Many2one(
        'uom.uom', 'Unit of Measure',
        required=True, states={'done': [('readonly', True)]}, domain=lambda self: self._get_domain_product_uom_id(),
        default=lambda self: self._get_scrap_uom())
    date_scrap = fields.Date()

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            pass

    @api.onchange('product_id')
    def _get_domain_product_uom_id(self):
        unit_measure = self.env.ref('uom.product_uom_unit').id
        # product_uom = self.product_id.uom_id.id
        return {'domain': {'product_uom_id': [('id', 'in', [unit_measure])]}}

    def action_validate(self):
        self.date_scrap = date.today()
        super(StockScrap, self).action_validate()
