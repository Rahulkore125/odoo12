from datetime import date

from odoo import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_confirm(self):
        result = super(SaleOrder, self).action_confirm()
        invoice_id = self.action_invoice_create(grouped=False, final=False)

        for e in invoice_id:
            invoice = self.env['account.invoice'].browse(e)
            invoice.update({
                'original_invoice': True,
                'order_id': self.id
            })

            invoice.action_invoice_open()
            if self.payment_method == 'cod':
                journal_id = self.env['account.journal'].search([('code', '=', 'CSH1')]).id
            elif self.payment_method == 'online_payment':
                journal_id = self.env['account.journal'].search([('code', '=', 'BNK1')]).id
            payment = self.env['account.payment'].create({
                'invoice_ids': [(4, e, None)],
                'amount': invoice.amount_total,
                'payment_date': date.today(),
                'communication': invoice.number,
                'payment_type': 'inbound',
                'journal_id': journal_id,
                'partner_type': 'customer',
                'payment_method_id': 1,
                'partner_id': invoice.partner_id.id
            })
            payment.action_validate_invoice_payment()

        return result

