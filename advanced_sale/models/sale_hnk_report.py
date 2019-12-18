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
        shopee = self.env.ref('advanced_sale.shopee').id
        pos = self.env.ref('advanced_sale.pos').id
        lazmall = self.env.ref('advanced_sale.lazmall').id
        lalafood = self.env.ref('advanced_sale.lalafood').id

        # handle stock
        today_date = fields.Datetime.to_datetime(self.datetime_report)
        previous_day_date = fields.Datetime.to_datetime(self.datetime_report) + timedelta(days=-1)
        heineken_product = self.env['product.product'].search([('is_heineken_product', '=', True)])
        qty_previous_day = self.env['product.product'].browse(heineken_product.ids)._compute_quantities_dict(
            self._context.get('lot_id'),
            self._context.get(
                'owner_id'),
            self._context.get(
                'package_id'),
            self._context.get(
                'from_date'),
            to_date=previous_day_date)
        qty_today = self.env['product.product'].browse(heineken_product.ids)._compute_quantities_dict(
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
                product_ids[e]['returned'] = 0
                product_ids[e]['amount_discount'] = 0
            else:
                product_ids[e] = {
                    'product_id': e,
                    'product_category_id': product.categ_id.id,
                    'sum_sale_chanel': 0,
                    'sum_fp_chanel': 0,
                    'sum_grab_chanel': 0,
                    'sum_shopee_chanel': 0,
                    'sum_lazmall_chanel': 0,
                    'sum_pos_chanel': 0,
                    'sum_lalafood_chanel': 0,
                    'amount_sale_cod': 0,
                    'amount_sale_ol': 0,
                    'amount_fp_cod': 0,
                    'amount_fp_ol': 0,
                    'amount_shopee_cod': 0,
                    'amount_shopee_ol': 0,
                    'amount_pos_cod': 0,
                    'amount_pos_ol': 0,
                    'amount_lazmall_cod': 0,
                    'amount_lazmall_ol': 0,
                    'amount_lalafood_cod': 0,
                    'amount_lalafood_ol': 0,
                    'amount_grab_cod': 0,
                    'amount_grab_ol': 0,
                    'open_stock': qty_previous_day[e]['qty_available'],
                    'close_stock': qty_today[e]['qty_available'],
                    'open_stock_units': qty_previous_day[e]['qty_available'] * precision,
                    'close_stock_units': qty_today[e]['qty_available'] * precision,
                    'damaged': 0,
                    'returned': 0,
                    'amount_discount': 0
                }

        for sale_order in sale_orders:
            for sale_order_line in sale_order.order_line:
                if not sale_order_line.is_reward_line and not sale_order_line.is_delivery:
                    # handle sale
                    if sale_order_line.product_id.id in product_ids:
                        # handle amount and quantity
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
                                    'amount_fp_ol'] += sale_order_line.price_subtotal
                        elif sale_order.team_id.id == grab:
                            product_ids[sale_order_line.product_id.id][
                                'sum_grab_chanel'] += sale_order_line.product_uom_qty
                            if sale_order.payment_method == 'cod':
                                product_ids[sale_order_line.product_id.id][
                                    'amount_grab_cod'] += sale_order_line.price_subtotal
                            elif sale_order.payment_method == 'online_payment':
                                product_ids[sale_order_line.product_id.id][
                                    'amount_grab_ol'] += sale_order_line.price_subtotal
                        elif sale_order.team_id.id == shopee:
                            product_ids[sale_order_line.product_id.id][
                                'sum_shopee_chanel'] += sale_order_line.product_uom_qty
                            if sale_order.payment_method == 'cod':
                                product_ids[sale_order_line.product_id.id][
                                    'amount_shopee_cod'] += sale_order_line.price_subtotal
                            elif sale_order.payment_method == 'online_payment':
                                product_ids[sale_order_line.product_id.id][
                                    'amount_shopee_ol'] += sale_order_line.price_subtotal
                        elif sale_order.team_id.id == pos:
                            product_ids[sale_order_line.product_id.id][
                                'sum_pos_chanel'] += sale_order_line.product_uom_qty
                            if sale_order.payment_method == 'cod':
                                product_ids[sale_order_line.product_id.id][
                                    'amount_pos_cod'] += sale_order_line.price_subtotal
                            elif sale_order.payment_method == 'online_payment':
                                product_ids[sale_order_line.product_id.id][
                                    'amount_pos_ol'] += sale_order_line.price_subtotal
                        elif sale_order.team_id.id == lazmall:
                            product_ids[sale_order_line.product_id.id][
                                'sum_lazmall_chanel'] += sale_order_line.product_uom_qty
                            if sale_order.payment_method == 'cod':
                                product_ids[sale_order_line.product_id.id][
                                    'amount_lazmall_cod'] += sale_order_line.price_subtotal
                            elif sale_order.payment_method == 'online_payment':
                                product_ids[sale_order_line.product_id.id][
                                    'amount_lazmall_ol'] += sale_order_line.price_subtotal
                        elif sale_order.team_id.id == lalafood:
                            product_ids[sale_order_line.product_id.id][
                                'sum_lalafood_chanel'] += sale_order_line.product_uom_qty
                            if sale_order.payment_method == 'cod':
                                product_ids[sale_order_line.product_id.id][
                                    'amount_lalafood_cod'] += sale_order_line.price_subtotal
                            elif sale_order.payment_method == 'online_payment':
                                product_ids[sale_order_line.product_id.id][
                                    'amount_lalafood_ol'] += sale_order_line.price_subtotal
                        # handle amount discount
                        print(product_ids[sale_order_line.product_id.id])
                        product_ids[sale_order_line.product_id.id][
                            'amount_discount'] += sale_order_line.price_subtotal * sale_order_line.discount / 100

                    # else:
                    #     product_ids[sale_order_line.product_id.id] = {
                    #         'product_id': sale_order_line.product_id.id,
                    #         'sum_sale_chanel': sale_order_line.product_uom_qty if sale_order.team_id.id == sale else 0,
                    #         'sum_fp_chanel': sale_order_line.product_uom_qty if sale_order.team_id.id == food_panda else 0,
                    #         'sum_grab_chanel': sale_order_line.product_uom_qty if sale_order.team_id.id == grab else 0,
                    #         'amount_sale_cod': sale_order_line.price_subtotal if sale_order.team_id.id == sale and sale_order.payment_method == 'cod' else 0,
                    #         'amount_sale_ol': sale_order_line.price_subtotal if sale_order.team_id.id == sale and sale_order.payment_method == 'online_payment' else 0,
                    #         'amount_fp_cod': sale_order_line.price_subtotal if sale_order.team_id.id == food_panda and sale_order.payment_method == 'cod' else 0,
                    #         'amount_fp_ol': sale_order_line.price_subtotal if sale_order.team_id.id == food_panda and sale_order.payment_method == 'online_payment' else 0,
                    #         'amount_grab': sale_order_line.price_subtotal if sale_order.team_id.id == grab else 0,
                    #         'amount_shopee_cod': sale_order_line.price_subtotal if sale_order.team_id.id == shopee and sale_order.payment_method == 'cod' else 0,
                    #         'amount_shopee_ol': sale_order_line.price_subtotal if sale_order.team_id.id == shopee and sale_order.payment_method == 'online_payment' else 0,
                    #         'amount_pos_cod': sale_order_line.price_subtotal if sale_order.team_id.id == pos and sale_order.payment_method == 'cod' else 0,
                    #         'amount_pos_ol': sale_order_line.price_subtotal if sale_order.team_id.id == pos and sale_order.payment_method == 'online_payment' else 0,
                    #         'amount_lazmall_cod': sale_order_line.price_subtotal if sale_order.team_id.id == lazmall and sale_order.payment_method == 'cod' else 0,
                    #         'amount_lazmall_ol': sale_order_line.price_subtotal if sale_order.team_id.id == lazmall and sale_order.payment_method == 'online_payment' else 0,
                    #         'amount_lalafood_cod': sale_order_line.price_subtotal if sale_order.team_id.id == food_panda and sale_order.payment_method == 'cod' else 0,
                    #         'amount_lalafood_ol': sale_order_line.price_subtotal if sale_order.team_id.id == food_panda and sale_order.payment_method == 'online_payment' else 0,
                    #     }

        scrap = self.env['stock.scrap'].search([('date_scrap', '=', self.date_report)])
        for e in scrap:
            product_ids[e.product_id.id]['damaged'] += e.scrap_qty
        return_picking = self.env['stock.picking'].search(
            [('date_return', '=', self.date_report), ('is_return_picking', '=', True)])
        for e in return_picking:
            for f in e.move_ids_without_package:
                if not f.scrapped:
                    product_ids[f.product_id.id]['returned'] += f.product_uom_qty

        self.env['sale.hnk.report.line'].search([]).unlink()

        for e in product_ids:
            values.append([0, 0, product_ids[e]])
        res = self.env['sale.hnk.report'].create({
            'date_report': self.date_report,
            'report_line_ids': values
        })

        self.env['sale.hnk.report'].search([('id', '!=', res.id)]).unlink()
        tree_view_id = self.env.ref('advanced_sale.sale_hnk_report_line_tree').id
        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree')],
            'view_mode': 'tree',
            'name': 'Sale & Stock Report',
            'res_model': 'sale.hnk.report.line',
            'domain': [('sale_report_id', '=', res.id)],
            'context': {'search_default_group_category_id': 1},
            'target': 'main'
        }
        return action


class SaleHnkReportLine(models.Model):
    _name = 'sale.hnk.report.line'

    product_id = fields.Many2one('product.product', string="Product")
    product_category_id = fields.Many2one('product.category', string="Product Category")
    open_stock = fields.Float("Opening Stock")
    open_stock_units = fields.Float(string="UNITS btls/cans (Opening)")

    damaged = fields.Float(string="Damaged(UNITS btls/cans)")
    returned = fields.Float(string="Return")

    sum_sale_chanel = fields.Float(string="Sold Drinkies")
    sum_fp_chanel = fields.Float(string="Sold FP")
    sum_grab_chanel = fields.Float(string="Sold Grab")
    sum_shopee_chanel = fields.Float(string="Sold Shopee")
    sum_pos_chanel = fields.Float(string="Sold POS")
    sum_lazmall_chanel = fields.Float(string="Sold Lazmall")
    sum_lalafood_chanel = fields.Float(string="Sold Lalafood")

    amount_sale_cod = fields.Float(string="Amount Drinkies COD")
    amount_sale_ol = fields.Float(string="Amount Drinkies Online")

    amount_fp_cod = fields.Float(string="Amount FP COD")
    amount_fp_ol = fields.Float(string="Amount FP Online")

    amount_grab_cod = fields.Float(string="Amount Grab COD")
    amount_grab_ol = fields.Float(string="Amount Grab Online")

    amount_shopee_cod = fields.Float(string="Amount Shopee COD")
    amount_shopee_ol = fields.Float(string="Amount Shopee Online")

    amount_pos_cod = fields.Float(string="Amount POS COD")
    amount_pos_ol = fields.Float(string="Amount POS Online")

    amount_lazmall_cod = fields.Float(string="Amount Lazmall COD")
    amount_lazmall_ol = fields.Float(string="Amount Lazmall Online")

    amount_lalafood_cod = fields.Float(string="Amount Lalafood COD")
    amount_lalafood_ol = fields.Float(string="Amount Lalafood Online")

    close_stock = fields.Float(string="Closing Stock")
    close_stock_units = fields.Float(string="UNITS btls/cans (Closing)")
    amount_discount = fields.Float(string="Amount Discount")
    sale_report_id = fields.Many2one('sale.hnk.report')
