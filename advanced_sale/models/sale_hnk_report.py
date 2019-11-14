from datetime import date, datetime
import pytz
from odoo import models, fields


class SaleHnkReport(models.Model):
    _name = 'sale.hnk.report'

    date_report = fields.Date(string="Date Report")
    report_line_ids = fields.One2many(comodel_name='sale.hnk.report.line', inverse_name='sale_report_id',
                                      string="Report Line")
    datetime_report = fields.Datetime(string="Datetime Report")

    def generate_report(self):
        local_tz = pytz.timezone(
            self.env.user.partner_id.tz or 'GMT')

        self.date_report = date(year=self.datetime_report.year, month=self.datetime_report.month,
                                day=self.datetime_report.day)


        sale_orders = self.env['sale.order'].search([('date_confirm_order', '=', self.date_report)])
        stock_picking = self.env['stock.picking'].search([('date_done_delivery', '=', self.date_report)])
        values = []


        product_ids = {}

        sale = self.env.ref('advanced_sale.sale').id
        food_panda = self.env.ref('advanced_sale.food_panda').id
        grab = self.env.ref('advanced_sale.grab').id

        for sale_order in sale_orders:
            for sale_order_line in sale_order.order_line:
                if not sale_order_line.is_reward_line and not sale_order_line.is_delivery:
                    if sale_order_line.product_id.id in product_ids:
                        if sale_order.team_id.id == sale:
                            product_ids[sale_order_line.product_id.id][
                                'sum_sale_chanel'] += sale_order_line.product_uom_qty
                            if sale_order.payment_method == 'cod':
                                product_ids[sale_order_line.product_id.id][
                                    'amount_sale_cod'] += sale_order_line.price_subtotal
                            elif sale_order.payment_method == 'online_payment':
                                product_ids[sale_order_line.product_id.id][
                                    'amount_sale_ol'] += sale_order_line.price_subtotal
                        elif sale_order.team_id.id == food_panda:
                            product_ids[sale_order_line.product_id.id][
                                'sum_fp_chanel'] += sale_order_line.product_uom_qty
                            if sale_order.payment_method == 'cod':
                                product_ids[sale_order_line.product_id.id][
                                    'amount_fp_cod'] += sale_order_line.price_subtotal
                            elif sale_order.payment_method == 'online_payment':
                                product_ids[sale_order_line.product_id.id][
                                    'amount_fp_online'] += sale_order_line.price_subtotal
                        elif sale_order.team_id.id == grab:
                            product_ids[sale_order_line.product_id.id][
                                'sum_grab_chanel'] += sale_order_line.product_uom_qty
                            product_ids[sale_order_line.product_id.id][
                                'amount_grab'] += sale_order_line.price_subtotal

                    else:
                        product_ids[sale_order_line.product_id.id] = {
                            'product_id': sale_order_line.product_id.id,
                            'sum_sale_chanel': sale_order_line.product_uom_qty if sale_order.team_id.id == sale else 0,
                            'sum_fp_chanel': sale_order_line.product_uom_qty if sale_order.team_id.id == food_panda else 0,
                            'sum_grab_chanel': sale_order_line.product_uom_qty if sale_order.team_id.id == grab else 0,
                            'amount_sale_cod': sale_order_line.price_subtotal if sale_order.team_id.id == sale and sale_order.payment_method == 'cod' else 0,
                            'amount_sale_ol': sale_order_line.price_subtotal if sale_order.team_id.id == sale and sale_order.payment_method == 'online_payment' else 0,
                            'amount_fp_cod': sale_order_line.price_subtotal if sale_order.team_id.id == food_panda and sale_order.payment_method == 'cod' else 0,
                            'amount_fp_online': sale_order_line.price_subtotal if sale_order.team_id.id == food_panda and sale_order.payment_method == 'online_payment' else 0,
                            'amount_grab': sale_order_line.price_subtotal if sale_order.team_id.id == grab else 0,
                        }
        product_id_array = []
        print(product_ids)
        for e in product_ids:
            values.append([0, 0, product_ids[e]])
            product_id_array.append(e)
        # res = self.env['sale.hnk.report'].create({
        #     'date_report': self.date_report,
        #     'report_line_ids': values
        # })

        # tree_view_id = self.env.ref('advanced_sale.sale_hnk_report_line_tree').id
        # action = {
        #     'type': 'ir.actions.act_window',
        #     'views': [(tree_view_id, 'tree')],
        #     'view_mode': 'tree',
        #     'name': 'Sale & Stock Report',
        #     'res_model': 'sale.hnk.report.line',
        #     'domain': [('sale_report_id', '=', res.id)]
        # }
        # return action
        to_date = self.datetime_report.astimezone(local_tz)
        to_date = fields.Datetime.to_datetime(to_date)
        qty = self.env['product.product'].browse(product_id_array)._compute_quantities_dict(self._context.get('lot_id'),
                                                                   self._context.get('owner_id'),
                                                                   self._context.get('package_id'),
                                                                   self._context.get('from_date'),
                                                                   to_date=to_date)
        print(qty)


class SaleHnkReportLine(models.Model):
    _name = 'sale.hnk.report.line'

    product_id = fields.Many2one('product.product', string="Product")
    open_stock = fields.Float("Opening Stock")
    open_stock_units = fields.Float(string="UNITS btls/cans (Opening)")
    damaged = fields.Float(string="Damaged")

    sum_sale_chanel = fields.Float(string="Sold")
    sum_fp_chanel = fields.Float(string="Sold FP")
    sum_grab_chanel = fields.Float(string="Sold Grab")

    amount_sale_cod = fields.Float(string="Amount Sale COD")
    amount_sale_ol = fields.Float(string="Amount Sale Online")
    amount_fp_cod = fields.Float(string="Amount FP COD")
    amount_fp_online = fields.Float(string="Amount FP Online")
    amount_grab = fields.Float(string="Amount Grab")

    close_stock = fields.Float(string="Closing Stock")
    close_stock_units = fields.Float(string="UNITS btls/cans (Closing)")
    amount_discount = fields.Float(string="Amount Discount")
    sale_report_id = fields.Many2one('sale.hnk.report')
