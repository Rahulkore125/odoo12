from odoo import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_confirm(self):
        result = super(SaleOrder, self).action_confirm()
        for so in self:
            stock_pickings = self.env['stock.picking'].search(
                [('sale_id', '=', so.id), ('picking_type_id.code', '=', 'outgoing')])
            for stock_picking in stock_pickings:
                for move_line in stock_picking.move_line_ids:
                    move_line.qty_done = move_line.product_uom_qty
                stock_picking.action_done()
        return result


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def onchange_unit_price(self):
        print(self.order_id.partner_id)
        print(self.product_id)
        if self.product_id.id and not self.order_id.partner_id:
            self.price_unit = self.product_id.list_price
