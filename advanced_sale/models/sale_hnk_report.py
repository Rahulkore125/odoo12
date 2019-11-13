from odoo import models, fields


class SaleHnkReport(models.Model):
    _name = 'sale.hnk.report'

    date_report = fields.Date(string="Date Report")
    report_line_ids = fields.One2many(comodel_name='sale.hnk.report.line', inverse_name='sale_report_id',
                                      string="Report Line")

    def generate_report(self):
        sale_orders = self.env['sale.order'].search([('date_confirm_order', '=', self.date_report)])
        stock_picking = self.env['stock.picking'].search([('date_done_delivery', '=', self.date_report)])


class SaleHnkReportLine(models.Model):
    _name = 'sale.hnk.report.line'

    product_id = fields.Many2one('product.product', string="Product")
    open_stock = fields.Float("Opening Stock")
    open_stock_units = fields.Float(string="UNITS btls/cans (Opening)")
    damaged = fields.Float(string="Damaged")
    close_stock = fields.Float(string="Closing Stock")
    close_stock_units = fields.Float(string="UNITS btls/cans (Closing)")
    amount_discount = fields.Float(string="Amount Discount")
    sale_report_id = fields.Many2one('sale.hnk.report')
