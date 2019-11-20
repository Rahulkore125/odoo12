from datetime import date, timedelta

from odoo import models, fields


class SaleHnkReport(models.Model):
    _name = 'sale.hnk.report'

    date_report = fields.Date(string="Date Report", default=fields.Date.today)
    report_line_ids = fields.One2many(comodel_name='sale.hnk.report.line', inverse_name='sale_report_id',
                                      string="Report Line")
    datetime_report = fields.Datetime(string="Datetime Report")

    def generate_report(self):
        self.date_report = date(year=self.datetime_report.year, month=self.datetime_report.month,
                                day=self.datetime_report.day)

        sale_orders = self.env['sale.order'].search([('date_confirm_order', '=', self.date_report)])
        values = []

        product_ids = {}

        sale = self.env.ref('advanced_sale.sale').id
        food_panda = self.env.ref('advanced_sale.food_panda').id
        grab = self.env.ref('advanced_sale.grab').id

        #handle stock
        today_date = fields.Datetime.to_datetime(self.datetime_report)
        previous_day_date = fields.Datetime.to_datetime(self.datetime_report) + timedelta(days=-1)
        all_product = self.env['product.product'].search([])
        qty_previous_day = self.env['product.product'].browse(all_product.ids)._compute_quantities_dict(
            self._context.get('lot_id'),
            self._context.get(
                'owner_id'),
            self._context.get(
                'package_id'),
            self._context.get(
                'from_date'),
            to_date=previous_day_date)
        qty_today = self.env['product.product'].browse(all_product.ids)._compute_quantities_dict(
            self._context.get('lot_id'),
            self._context.get(
                'owner_id'),
            self._context.get(
                'package_id'),
            self._context.get(
                'from_date'),
            to_date=today_date)
        for e in qty_today:
            product = self.env['product.product'].browse(e)
            precision = product.uom_id.factor_inv
            if e in product_ids:
                product_ids[e]['product_category_id'] = product.categ_id.id,
                product_ids[e]['close_stock'] = qty_today[e]['qty_available']
                product_ids[e]['open_stock'] = qty_previous_day[e]['qty_available']
                product_ids[e]['open_stock_units'] = product_ids[e]['open_stock'] * precision
                product_ids[e]['close_stock_units'] = product_ids[e]['close_stock'] * precision
                product_ids[e]['damaged'] = 0
                product_ids[e]['amount_discount'] = 0
            else:
                product_ids[e] = {
                    'product_id': e,
                    'product_category_id': product.categ_id.id,
                    'sum_sale_chanel': 0,
                    'sum_fp_chanel': 0,
                    'sum_grab_chanel': 0,
                    'amount_sale_cod': 0,
                    'amount_sale_ol': 0,
                    'amount_fp_cod': 0,
                    'amount_fp_online': 0,
                    'amount_grab': 0,
                    'open_stock': qty_previous_day[e]['qty_available'],
                    'close_stock': qty_today[e]['qty_available'],
                    'open_stock_units': qty_previous_day[e]['qty_available'] * precision,
                    'close_stock_units': qty_today[e]['qty_available'] * precision,
                    'damaged': 0,
                    'amount_discount': 0
                }

        for sale_order in sale_orders:

            for sale_order_line in sale_order.order_line:

                if not sale_order_line.is_reward_line and not sale_order_line.is_delivery:
                    # handle sale
                    if sale_order_line.product_id.id in product_ids:
                        #handle amount and quantity
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
                        #handle amount discount
                        product_ids[sale_order_line.product_id.id]['amount_discount'] += sale_order_line.price_subtotal*sale_order_line.discount/100

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
                # handle amount discount
            #handle damaged
            pickings = sale_order.picking_ids
            for picking in pickings:
                scrap = self.env['stock.scrap'].search([('picking_id', '=', picking.id)])
                for e in scrap:
                    product_ids[e.product_id.id]['damaged'] += e.scrap_qty



        for e in product_ids:
            values.append([0, 0, product_ids[e]])
        res = self.env['sale.hnk.report'].create({
            'date_report': self.date_report,
            'report_line_ids': values
        })

        tree_view_id = self.env.ref('advanced_sale.sale_hnk_report_line_tree').id
        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree')],
            'view_mode': 'tree',
            'name': 'Sale & Stock Report',
            'res_model': 'sale.hnk.report.line',
            'domain': [('sale_report_id', '=', res.id)],
            'context': {'search_default_group_category_id': 1}
        }
        return action


class SaleHnkReportLine(models.Model):
    _name = 'sale.hnk.report.line'

    product_id = fields.Many2one('product.product', string="Product")
    product_category_id = fields.Many2one('product.category', string="Product Category")
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
