from odoo import fields, models

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    date_done_delivery = fields.Date()


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def create_returns(self):
        for wizard in self:
            new_picking_id, pick_type_id = wizard._create_returns()
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
        action = self.env['sale.order'].browse(picking.sale_id.id).action_view_delivery()

        return action


class StockMove(models.Model):
    _inherit = "stock.move"

    to_refund = fields.Boolean(string="To Refund (update SO/PO)", copy=False,
                               help='Trigger a decrease of the delivered/received quantity in the associated Sale Order/Purchase Order',
                               default=True)
