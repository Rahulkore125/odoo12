from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    estimate_discount_total = fields.Monetary(string='Additional Whole Order Discount')
    computed_discount_total = fields.Monetary(string='Discount Total', compute='compute_discount_total')
    payment_method = fields.Selection(string="Payment Method",
                                      selection=[('cod', 'COD'), ('online_payment', 'Online Payment'), ],
                                      required=False, default="cod")

    @api.multi
    @api.onchange('estimate_discount_total')
    def compute_discount_order_line(self):
        for rec in self:
            sum = 0
            for e in rec.order_line:
                if not e.is_reward_line and not e.is_delivery:
                    sum += e.price_subtotal
            if sum > 0:
                each_line_order_discount = rec.estimate_discount_total / sum * 100
                for e in rec.order_line:
                    if not e.is_reward_line and not e.is_delivery:
                        e.discount = each_line_order_discount

    @api.multi
    @api.depends('order_line', 'estimate_discount_total')
    def compute_discount_total(self):
        for rec in self:
            sum = 0
            for e in rec.order_line:
                if e.is_reward_line:
                    sum += abs(e.price_subtotal)
            sum += rec.estimate_discount_total
            rec.computed_discount_total = sum

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

    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            amount_reward = 0.0
            for line in order.order_line:
                if not line.is_reward_line:
                    amount_untaxed += line.price_subtotal
                else:
                    amount_reward += line.price_subtotal
                amount_tax += line.price_tax

            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax - order.computed_discount_total
            })


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def onchange_unit_price(self):
        if self.product_id.id and not self.order_id.partner_id:
            self.price_unit = self.product_id.list_price

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                            product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
