import datetime

import math

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ...utils.magento.customer import Customer, CustomerGroup
from ...utils.magento.product import Product
from ...utils.magento.rest import Client
from ...utils.magento.sales import Order

TYPE2JOURNAL = {
    'out_invoice': 'sale',
    'in_invoice': 'purchase',
    'out_refund': 'sale',
    'in_refund': 'purchase',
}


def get_current_page(total_count, page_size):
    # print("total count la:",total_count)
    total_page = total_count / page_size
    # print("how to page size:",page_size)
    if 0 < total_page < 1:
        total_page = 1
    else:
        total_page = math.ceil(total_page)
    # print("total page la:",total_page)
    return total_page


class MagentoBackend(models.Model):

    # @api.model
    # def _default_journal(self):
    #     if self._context.get('default_journal_id', False):
    #         return self.env['account.journal'].browse(self._context.get('default_journal_id'))
    #     inv_type = self._context.get('type', 'out_invoice')
    #     inv_types = inv_type if isinstance(inv_type, list) else [inv_type]
    #     company_id = self._context.get('company_id', self.env.user.company_id.id)
    #     domain = [
    #         ('type', 'in', [TYPE2JOURNAL[ty] for ty in inv_types if ty in TYPE2JOURNAL]),
    #         ('company_id', '=', company_id),
    #     ]
    #     journal_with_currency = False
    #     if self._context.get('default_currency_id'):
    #         currency_clause = [('currency_id', '=', self._context.get('default_currency_id'))]
    #         journal_with_currency = self.env['account.journal'].search(domain + currency_clause, limit=1)
    #     return journal_with_currency or self.env['account.journal'].search(domain, limit=1)

    _name = "magento.backend"

    name = fields.Char(string='Name', required=True)
    version = fields.Selection(selection=([('Magento 2.3', '2.3'), ('Magento 2.2', '2.2')]), default='Magento 2.3',
                               string='Version', required=True)
    web_url = fields.Char(
        string='Url',
        required=True,
        help="Url to magento application",
    )
    access_token = fields.Char(string='Token', required=True, help="Access token to magento Integration")

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        readonly=True,
    )
    website_ids = fields.One2many('magento.website', 'backend_id', string='Website', readonly=True, )

    # Invoice
    # payment_journal = fields.Many2one('account.journal', string='Payment Journal', required=True,
    #                                   domain=[('type', 'in', ('bank', 'cash'))])
    # journal_id = fields.Many2one('account.journal', string='Journal', required=True, domain=[('type', '=', 'sale')])
    # prefix_invoice = fields.Char('Prefix Invoice')
    prefix_order = fields.Char('Prefix Order')
    # Page Size
    products_pageSize = fields.Integer(string='Products page size', required=True, default=500)

    customers_pageSize = fields.Integer(string='Customers page size', required=True, default=500)

    sale_orders_pageSize = fields.Integer(string='Sale oders page size', required=True, default=500)

    invoice_pageSize = fields.Integer(string='Invoice page size', required=True, default=500)

    # auto fetch
    auto_import_magento = fields.Boolean(string='Import Automatic', default=False)
    interval_number_import_magento = fields.Integer(string='Execute every', default=5)
    interval_type_import_magento = fields.Selection([('minutes', 'Minutes'),
                                                     ('hours', 'Hours'),
                                                     ('days', 'Days'),
                                                     ('weeks', 'Weeks'),
                                                     ('months', 'Months')], string='Interval Unit', default='months')
    nextcall_import_magento = fields.Datetime(string='Next execution date')
    auto_fetching = fields.Boolean(string='Fetching', default=False)
    # customers
    # auto_import_customers = fields.Boolean(string='Import Customers', default=False)
    # interval_number_import_customers = fields.Integer(string='Execute every')
    # interval_type_import_customers = fields.Selection([('minutes', 'Minutes'),
    #                                                    ('hours', 'Hours'),
    #                                                    ('days', 'Days'),
    #                                                    ('weeks', 'Weeks'),
    #                                                    ('months', 'Months')], string='Interval Unit', default='months')
    # nextcall_import_customers = fields.Datetime(string='Next execution date')
    #
    # # product
    # auto_import_products = fields.Boolean(string='Import Products', default=False)
    # interval_number_import_products = fields.Integer(string='Execute every')
    # interval_type_import_products = fields.Selection([('minutes', 'Minutes'),
    #                                                   ('hours', 'Hours'),
    #                                                   ('days', 'Days'),
    #                                                   ('weeks', 'Weeks'),
    #                                                   ('months', 'Months')], string='Interval Unit', default='months')
    # nextcall_import_products = fields.Datetime(string='Next execution date')
    #
    # # Sale orders
    # auto_import_sale_orders = fields.Boolean(string='Import Sale orders', default=False)
    # interval_number_import_sale_orders = fields.Integer(string='Execute every')
    # interval_type_import_sale_orders = fields.Selection([('minutes', 'Minutes'),
    #                                                      ('hours', 'Hours'),
    #                                                      ('days', 'Days'),
    #                                                      ('weeks', 'Weeks'),
    #                                                      ('months', 'Months')], string='Interval Unit',
    #                                                     default='months')
    # nextcall_import_sale_orders = fields.Datetime(string='Next execution date')
    #
    # # Invoice
    # auto_import_invoice = fields.Boolean(string='Import Sale orders', default=False)
    # interval_number_import_invoice = fields.Integer(string='Execute every')
    # interval_type_import_invoice = fields.Selection([('minutes', 'Minutes'),
    #                                                  ('hours', 'Hours'),
    #                                                  ('days', 'Days'),
    #                                                  ('weeks', 'Weeks'),
    #                                                  ('months', 'Months')], string='Interval Unit', default='months')
    # nextcall_import_invoice = fields.Datetime(string='Next execution date')

    _sql_constraints = [('uniq_web_url', 'unique(web_url)', "The Url must be unique !")]

    @api.constrains('interval_number_import_magento')
    def _contrains_interval_number_import_magento(self):
        if self.interval_number_import_magento <= 0:
            raise ValidationError("Time excute must be greater than 0")
        if type(self.interval_number_import_magento) == float:
            raise ValidationError("time excute very must be integer not float")

    @api.model
    def create(self, values):
        record = super(MagentoBackend, self).create(values)
        if values.get('web_url') and values.get('access_token'):
            access_token = values.get('access_token')
            url = values.get('web_url')
            self.pull_magento_backend(url, access_token, record.id)

        if values.get('auto_import_magento'):
            self._ir_cron(values.get('auto_import_magento'), values.get('interval_number_import_magento'),
                          values.get('interval_type_import_magento'), values.get('nextcall_import_magento'),
                          'ir_cron_pull_magento')
        # customers
        # if values.get('auto_import_customers'):
        #     self._ir_cron(values.get('auto_import_customers'), values.get('interval_number_import_customers'),
        #                   values.get('interval_type_import_customers'), values.get('nextcall_import_customers'),
        #                   'ir_cron_pull_customers')
        # #
        # # products
        # if values.get('auto_import_products'):
        #     self._ir_cron(values.get('auto_import_products'), values.get('interval_number_import_products'),
        #                   values.get('interval_type_import_products'), values.get('nextcall_import_products'),
        #                   'ir_cron_pull_products')
        #
        # # sale_orders
        # if values.get('auto_import_sale_orders'):
        #     self._ir_cron(values.get('auto_import_sale_orders'), values.get('interval_number_import_sale_orders'),
        #                   values.get('interval_type_import_sale_orders'), values.get('nextcall_import_sale_orders'),
        #                   'ir_cron_pull_orders')
        #
        # # invoice
        # if values.get('auto_import_invoice'):
        #     self._ir_cron(values.get('auto_import_invoice'), values.get('interval_number_import_invoice'),
        #                   values.get('interval_type_import_invoice'), values.get('nextcall_import_invoice'),
        #                   'ir_cron_pull_invoice')

        return record

    @api.multi
    def write(self, values):
        # ir cron write
        interval_number_import_magento = values.get('interval_number_import_magento') if values.get(
            'interval_number_import_magento', False) else self.interval_number_import_magento
        interval_type_import_magento = values.get('interval_type_import_magento') if values.get(
            'interval_type_import_magento', False) else self.interval_type_import_magento
        nextcall_import_magento = values.get('nextcall_import_magento') if values.get('nextcall_import_magento',
                                                                                      False) else self.nextcall_import_magento
        # auto_import_magento = values.get('auto_import_magento') if values.get('auto_import_magento',
        #                                                                           False) else self.auto_import_magento
        if 'auto_import_magento' in values:
            auto_import_magento = values.get('auto_import_magento')
            self._ir_cron(auto_import_magento, interval_number_import_magento, interval_type_import_magento,
                          nextcall_import_magento, 'ir_cron_pull_magento')
        # # customers
        # interval_number_import_customers = values.get('interval_number_import_customers') if values.get(
        #     'interval_number_import_customers', False) else self.interval_number_import_customers
        # interval_type_import_customers = values.get('interval_type_import_customers') if values.get(
        #     'interval_type_import_customers', False) else self.interval_type_import_customers
        # nextcall_import_customers = values.get('nextcall_import_customers') if values.get('nextcall_import_customers',
        #                                                                                   False) else self.nextcall_import_customers
        # # auto_import_customers = values.get('auto_import_customers') if values.get('auto_import_customers',
        # #                                                                           False) else self.auto_import_customers
        # if 'auto_import_customers' in values:
        #     auto_import_customers = values.get('auto_import_customers')
        #     self._ir_cron(auto_import_customers, interval_number_import_customers, interval_type_import_customers,
        #                   nextcall_import_customers, 'ir_cron_pull_customers')
        #
        # # sale orders
        # interval_number_import_sale_orders = values.get('interval_number_import_sale_orders') if values.get(
        #     'interval_number_import_sale_orders', False) else self.interval_number_import_sale_orders
        # interval_type_import_sale_orders = values.get('interval_type_import_sale_orders') if values.get(
        #     'interval_type_import_sale_orders', False) else self.interval_type_import_sale_orders
        # nextcall_import_sale_orders = values.get('nextcall_import_sale_orders') if values.get(
        #     'nextcall_import_sale_orders', False) else self.nextcall_import_sale_orders
        # # auto_import_sale_orders = values.get('auto_import_sale_orders') if values.get('auto_import_sale_orders',
        # #                                                                               False) else self.auto_import_sale_orders
        # if 'auto_import_sale_orders' in values:
        #     auto_import_sale_orders = values.get('auto_import_sale_orders')
        #     self._ir_cron(auto_import_sale_orders, interval_number_import_sale_orders, interval_type_import_sale_orders,
        #               nextcall_import_sale_orders, 'ir_cron_pull_orders')
        #
        # # invoice
        # interval_number_import_invoice = values.get('interval_number_import_invoice') if values.get(
        #     'interval_number_import_invoice', False) else self.interval_number_import_invoice
        # interval_type_import_invoice = values.get('interval_type_import_invoice') if values.get(
        #     'interval_type_import_invoice', False) else self.interval_type_import_invoice
        # nextcall_import_invoice = values.get('nextcall_import_invoice') if values.get('nextcall_import_invoice',
        #                                                                               False) else self.nextcall_import_invoice
        # # auto_import_invoice = values.get('auto_import_invoice') if values.get('auto_import_invoice',
        # #                                                                       False) else self.auto_import_invoice
        # if 'auto_import_invoice' in values:
        #     auto_import_invoice = values.get('auto_import_invoice')
        #     self._ir_cron(auto_import_invoice, interval_number_import_invoice, interval_type_import_invoice,
        #               nextcall_import_invoice, 'ir_cron_pull_invoice')

        # #products
        # interval_number_import_products = values.get('interval_number_import_products') if values.get(
        #     'interval_number_import_products', False) else self.interval_number_import_products
        # interval_type_import_products = values.get('interval_type_import_products') if values.get(
        #     'interval_type_import_products', False) else self.interval_type_import_products
        # nextcall_import_products = values.get('nextcall_import_products') if values.get('nextcall_import_products',
        #                                                                               False) else self.nextcall_import_products
        # auto_import_products = values.get('auto_import_products') if values.get('auto_import_products',
        #                                                                       False) else self.auto_import_products
        # self._ir_cron(auto_import_products, interval_number_import_products, interval_type_import_products,
        #               nextcall_import_products, 'ir_cron_pull_products')
        #
        return super(MagentoBackend, self).write(values)

    @api.multi
    def unlink(self):
        self.env.cr.execute(""" DELETE FROM magento_res_partner_category WHERE TRUE;
                                DELETE FROM magento_address WHERE TRUE;
                                DELETE FROM magento_res_partner WHERE TRUE;
                                DELETE FROM res_partner WHERE is_from_magento = TRUE;
                                DELETE FROM magento_website WHERE TRUE;
                                DELETE FROM magento_pull_history WHERE TRUE;
                                DELETE FROM magento_sale_order WHERE TRUE;
                                DELETE FROM sale_order WHERE TRUE;
                                DELETE FROM magento_account_invoice WHERE TRUE;
                                DELETE FROM magento_backend WHERE TRUE;
                                DELETE FROM res_partner WHERE id > 50;
                                DELETE FROM magento_storeview WHERE TRUE;
                                DELETE FROM magento_store WHERE TRUE;
                                DELETE FROM res_partner_category WHERE TRUE;""")

    def _ir_cron(self, auto_import, interval_number, interval_type, nextcall, id):
        if auto_import:
            self.env.ref('magento2_connector.' + str(id)).write({
                'interval_number': interval_number,
                'interval_type': interval_type,
                'nextcall': nextcall,
                'numbercall': -1,
                'priority': 1,
                'active': True
            })
        else:
            self.env.ref('magento2_connector.' + str(id)).write({
                'numbercall': 0,
                'active': False,
            })

    def pull_magento_backend(self, url, access_token, backend_id):
        # try:
            if 'https' in url:
                client = Client(url, access_token, True)
            else:
                client = Client(url, access_token, False)
            # website
            websites = client.call('rest/V1/store/websites', '')

            website_magento_id = []
            website_odoo_id = []
            check_len_arr = False
            for website in websites:
                self.env.cr.execute("""INSERT INTO magento_website (name, code,backend_id,external_id,create_date, write_date,create_uid,write_uid)
                                        VALUES (%s, %s, %s, %s, %s ,%s, %s, %s) ON CONFLICT (backend_id, external_id) DO UPDATE SET (name,code)=(EXCLUDED.name,EXCLUDED.code) RETURNING id""",
                                    (website['name'], website['code'], backend_id, website['id'],
                                     datetime.datetime.today(), datetime.datetime.today(), self.env.uid, self.env.uid))

                # web = self.env['magento.website'].create({
                #     'name': website['name'],
                #     'code': website['code'],
                #     'backend_id': backend_id,
                #     'external_id': website['id']
                # })
                web_id = self.env.cr.fetchall()[0][0]
                website_magento_id.append(website['id'])
                website_odoo_id.append(web_id)

            # filter(lambda x, y: x == y, website_odoo_id, website_magento_id)

            if len(website_odoo_id) == len(website_magento_id):
                check_len_arr = True

            # store
            store_groups = client.call('rest/V1/store/storeGroups', '')
            for store_group in store_groups:
                self.env.cr.execute("""INSERT INTO magento_store (name, code, root_category_id, website_id, backend_id, external_id)
                                       VALUES (%s, %s, %s, %s, %s, %s ) ON CONFLICT (backend_id, external_id) DO UPDATE SET (name, code, root_category_id, website_id) = (EXCLUDED.name, EXCLUDED.code, EXCLUDED.root_category_id, EXCLUDED.website_id)""",
                                    (store_group['name'], store_group['code'] if 'code' in store_group else '',
                                     store_group['root_category_id'], website_odoo_id[
                                         website_magento_id.index(store_group['website_id'])] if check_len_arr else -1,
                                     backend_id, store_group['id']))
            # store view
            store_views = client.call('/rest/V1/store/storeViews', '')
            for store_view in store_views:
                self.env.cr.execute("""INSERT INTO magento_storeview (name,code,store_id,website_id,is_active,backend_id, external_id)
                                                       VALUES (%s, %s, %s, %s, %s, %s, %s ) ON CONFLICT (backend_id, external_id) DO UPDATE SET (name, code, store_id, website_id, is_active) =(EXCLUDED.name, EXCLUDED.code, EXCLUDED.store_id, EXCLUDED.website_id, EXCLUDED.is_active)  """,
                                    (store_view['name'], store_view['code'] if 'code' in store_view else '',
                                     client.adapter_magento_id('magento_store', backend_id,
                                                               store_view['store_group_id'], self),
                                     website_odoo_id[
                                         website_magento_id.index(store_view['website_id'])] if check_len_arr else -1,
                                     store_view['is_active'] if 'is_active' in store_view else 1, backend_id, store_view['id']))
        # except Exception as e:
        #     raise UserError(_('Not pull data from magento - magento.backend %s') % tools.ustr(e))

    def fetch_customers(self):
        self.env.cr.execute("DELETE FROM sale_order")
        self.env.cr.execute("DELETE FROM account_invoice")
        customers_delete = self.env['res.partner'].search([('create_date', '=', False)]).unlink()
        self._cr.execute("UPDATE magento_backend SET auto_fetching = False")
        # self._cr.execute("DELETE FROM magento_pull_history WHERE name=%s", ('normal_product',))
        # self._cr.execute("DELETE FROM magento_pull_history WHERE name=%s", ('customers',))


        # if not self.auto_fetching:
        #     # get from config
        #     if not self.id:
        #         self = self.env['magento.backend'].search([], limit=1)
        #     backend_id = self.id
        #     url = self.web_url
        #     token = self.access_token
        #     self.pull_magento_backend(url, token, backend_id)
        #
        #     page_size = self.customers_pageSize
        #     cus = Customer(url, token, True)
        #
        #     if page_size > 0:
        #         current_page = 0
        #         pull_history = self.env['magento.pull.history'].search(
        #             [('backend_id', '=', backend_id), ('name', '=', 'customers')])
        #
        #         if pull_history:
        #             # second pull
        #             sync_date = pull_history.sync_date
        #             customers = cus.list_gt_updated_at(sync_date)
        #             if len(customers['items']) > 0:
        #                 pull_history.write({
        #                     'sync_date': datetime.datetime.today()
        #                 })
        #
        #         else:
        #             # first pull
        #             self.env['magento.pull.history'].create({
        #                 'name': 'customers',
        #                 'sync_date': datetime.datetime.today(),
        #                 'backend_id': backend_id
        #             })
        #             customers = cus.list(page_size, current_page)
        #
        #         cus_group = CustomerGroup(url, token, True)
        #         customer_groups = cus_group.list_all()
        #         cus_group.insert(customer_groups, url, token, backend_id, self)
        #
        #         total_amount = customers['total_count']
        #         cus.insert(customers['items'], backend_id, url, token, self)
        #         total_page = total_amount / page_size
        #
        #         if 0 < total_page < 1:
        #             total_page = 1
        #         else:
        #             total_page = math.ceil(total_page)
        #
        #         for page in range(1, total_page):
        #             customers = cus.list(page_size, page + 1)
        #             cus.insert(customers['items'], backend_id, url, token, self)
        #
        #
        #
        #     return {
        #         'type': 'ir.actions.act_window',
        #         'view_type': 'form',
        #         'view_mode': 'form',
        #         'res_model': 'popup.dialog',
        #         'target': 'new',
        #         'context': {
        #             'default_message': "Fetch customers successful"
        #         },
        #     }
        # else:
        #     return {
        #         'type': 'ir.actions.act_window',
        #         'view_type': 'form',
        #         'view_mode': 'form',
        #         'res_model': 'popup.dialog',
        #         'target': 'new',
        #         'context': {
        #             'default_message': "Customers are fetching by schedule action, you can fetch customers manually after schedule action finish"
        #         },
        #     }

    def fetch_products(self):
        if not self.auto_fetching:
            # get from config
            if not self.id:
                self = self.env['magento.backend'].search([], limit=1)
            # fetch attr first
            self.fetch_product_attribute()
            backend_id = self.id
            url = self.web_url
            token = self.access_token

            pro = Product(url, token, True)

            page_size = self.products_pageSize

            # sync product category
            product_categories = pro.list_categories()
            pull_product_category_history = self.env['magento.pull.history'].search(
                [('backend_id', '=', backend_id), ('name', '=', 'categories')])
            if pull_product_category_history:
                # second pull
                pro.update_product_categories(product_categories, backend_id, self)
                pull_product_category_history.write({
                    'sync_date': datetime.datetime.today()
                })
            else:
                # first pull
                pro.insert_product_category(product_categories, backend_id, self)
                self.env['magento.pull.history'].create({
                    'name': 'categories',
                    'sync_date': datetime.datetime.today(),
                    'backend_id': backend_id
                })

            if page_size > 0:
                current_page = 0
                if self:
                    # pull_history_configurable_product = self.env['magento.pull.history'].search(
                    #     [('backend_id', '=', backend_id), ('name', '=', 'configurable_product')])
                    # # Configurbale Product
                    # # try:
                    # if pull_history_configurable_product:
                    #     # second pull
                    #     sync_date = pull_history_configurable_product.sync_date
                    #     products = pro.list_gt_updated_product(sync_date, 'eq')
                    #     if len(products['items']) > 0:
                    #         pull_history_configurable_product.write({
                    #             'sync_date': datetime.datetime.today()
                    #         })
                    #
                    # else:
                    #     # first pull
                    #     self.env['magento.pull.history'].create({
                    #         'name': 'configurable_product',
                    #         'sync_date': datetime.datetime.today(),
                    #         'backend_id': backend_id
                    #     })
                    #     products = pro.list_product(page_size, current_page, 'configurable', 'eq')
                    #
                    # total_count = products['total_count']
                    # pro.insert_configurable_product(products['items'], backend_id, url, token, self)
                    #
                    # total_page = get_current_page(total_count, page_size)
                    # if total_page > 0:
                    #     for page in range(1, total_page):
                    #         products = pro.list_product(page_size, page + 1, 'configurable', 'eq')
                    #         pro.insert_configurable_product(products['items'], backend_id, url, token)
                    # # except Exception as e:
                    # #     print(e)
                    # #     raise UserError(_('fetch product configurable %s or fetch product attribute') % tools.ustr(e))

                    # Normal Product
                    pull_history_normal_product = self.env['magento.pull.history'].search(
                        [('backend_id', '=', backend_id), ('name', '=', 'normal_product')])
                    # try:
                    if pull_history_normal_product:
                        sync_date = pull_history_normal_product.sync_date
                        products = pro.list_gt_updated_product(sync_date, 'neq')
                        if len(products['items']) > 0:
                            pull_history_normal_product.write({
                                'sync_date': datetime.datetime.today()
                            })
                    else:
                        # first pull
                        self.env['magento.pull.history'].create({
                            'name': 'normal_product',
                            'sync_date': datetime.datetime.today(),
                            'backend_id': backend_id
                        })
                        products = pro.list_product(page_size, current_page, 'configurable', 'neq')

                    total_count = products['total_count']
                    pro.insert_not_configurable_product(products['items'], backend_id, url, token, self)

                    total_page = get_current_page(total_count, page_size)
                    if total_page > 0:
                        for page in range(1, total_page):
                            # print('11111')
                            products = pro.list_product(page_size, page + 1, 'configurable', 'neq')
                            # print('22222')
                            pro.insert_not_configurable_product(products['items'], backend_id, url, token, self)
                            # print('333333')

                    # self.env['product.product.product'].create()
                    # else:
                    #     print("sai me roi")
                    # except Exception as e:
                    #     print(e)
                    #     raise UserError(_('fetch normal product %s') % tools.ustr(e))
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'popup.dialog',
                'target': 'new',
                'context': {
                    'default_message': "Fetch products successful"
                },
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'popup.dialog',
                'target': 'new',
                'context': {
                    'default_message': "Products are fetching by schedule action, you can fetch product manually after schedule action finish"
                },
            }

    def fetch_sale_orders(self):
        if not self.auto_fetching:
            if not self.id:
                self = self.env['magento.backend'].search([], limit=1)
            self.fetch_customers()
            self.fetch_tax()
            # self.fetch_invoice()

            backend_name = self.name
            backend_id = int(self.id)

            if not backend_id:
                first_backend = self.env['magento.backend'].search([], limit=1)
                if first_backend.id:
                    backend_id = first_backend.id
            url = self.web_url
            token = self.access_token
            prefix_order = self.prefix_order
            if prefix_order:
                prefix_order = prefix_order + '/'
            else:
                prefix_order = 'SO/Magento' + str(backend_id) + '/'

            page_size = self.sale_orders_pageSize
            order = Order(url, token, True)
            if page_size > 0:
                current_page = 0
                pull_history = self.env['magento.pull.history'].search(
                    [('backend_id', '=', backend_id), ('name', '=', 'sale_orders')])

                if pull_history:
                    # second pull
                    sync_date = pull_history.sync_date
                    orders = order.list_gt_updated_at(sync_date)
                    if len(orders['items']) > 0:
                        pull_history.write({
                            'sync_date': datetime.datetime.today()
                        })
                else:
                    # first pull
                    self.env['magento.pull.history'].create({
                        'name': 'sale_orders',
                        'sync_date': datetime.datetime.today(),
                        'backend_id': backend_id
                    })
                    orders = order.list(page_size, current_page)

                total_amount = orders['total_count']
                order.importer_sale(orders['items'], backend_id, backend_name, prefix_order, context=self)
                total_page = total_amount / page_size

                if 0 < total_page < 1:
                    total_page = 1
                else:
                    total_page = math.ceil(total_page)

                for page in range(1, total_page):
                    orders = order.list(page_size, page + 1)
                    order.importer_sale(orders['items'], backend_id, backend_name, prefix_order, context=self)

                # page_size = 10
                # # for page in range(1, total_page):
                # orders = order.list(page_size, 1)
                # order.importer_sale(orders['items'], backend_id, backend_name, prefix_order, context=self)

            # sync shipments
            # pull_shipments_history = self.env['magento.pull.history'].search(
            #     [('backend_id', '=', backend_id), ('name', '=', 'shipments')])
            # if pull_shipments_history:
            #     # second pull
            #     sync_date = pull_shipments_history.sync_date
            #     shipments = order.list_gt_update_at_shipment(sync_date)
            #     order.import_shipment(shipments, backend_id, context=self)
            #     if len(shipments) > 0:
            #         pull_shipments_history.write({
            #             'sync_date': datetime.datetime.today()
            #         })
            # else:
            #     # first pull
            #     shipments = order.listShipment()
            #     self.env['magento.pull.history'].create({
            #         'name': 'shipments',
            #         'sync_date': datetime.datetime.today(),
            #         'backend_id': backend_id
            #     })
            #     order.import_shipment(shipments, backend_id, context=self)
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'popup.dialog',
                'target': 'new',
                'context': {
                    'default_message': "Fetch sale orders successful"
                },
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'popup.dialog',
                'target': 'new',
                'context': {
                    'default_message': "Sale orders are fetching by schedule action, you can fetch sale orders manually after schedule action finish"
                },
            }

    # disable in this version
    def fetch_tax(self):
        backend_id = self.id
        url = self.web_url
        token = self.access_token
        magento_backend_name = self.name

        client = Client(url, token, True)

        account_tax_group_id = 1
        account_tax_group = self.env['account.tax.group'].search([('name', '=', magento_backend_name)], limit=1)
        if account_tax_group:
            account_tax_group_id = account_tax_group.id
        else:
            res = self.env['account.tax.group'].create({
                'name': magento_backend_name,
                'sequence': 10
            })
            account_tax_group_id = res.id

        # website
        tax_rates = client.call('/rest/V1/taxRates/search', 'searchCriteria')
        account_taxs = []
        for tax_rate in tax_rates['items']:
            if tax_rate['rate'] != 0:
                account_taxs.append((tax_rate['code'], tax_rate['rate'], 'sale', 'percent', 1, 1, account_tax_group_id,
                                     True, tax_rate['id'], backend_id))

        if account_taxs and len(account_taxs) > 0:
            self.env.cr.execute(
                """INSERT INTO account_tax (name, amount, type_tax_use, amount_type,company_id,sequence,tax_group_id, active, external_id, backend_id) VALUES {values} ON CONFLICT(external_id, backend_id) DO UPDATE SET (name, amount, active) = (EXCLUDED.name, EXCLUDED.amount, EXCLUDED.active) """
                    .format(values=", ".join(["%s"] * len(account_taxs))), tuple(account_taxs))
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'popup.dialog',
            'target': 'new',
            'context': {
                'default_message': "Fetch tax successful"
            },
        }

    def fetch_product_attribute(self):
        if not self.auto_fetching:
            if not self.id:
                self = self.env['magento.backend'].search([], limit=1)
            backend_id = self.id
            url = self.web_url
            token = self.access_token

            pro = Product(url, token, True)
            # Insert Product Attribute
            attributes = pro.list_attribute_type_select()['items']
            pro.insert_product_attribute(attributes, backend_id, context=self)
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'popup.dialog',
                'target': 'new',
                'context': {
                    'default_message': "Fetch product attribute successful"
                },
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'popup.dialog',
                'target': 'new',
                'context': {
                    'default_message': "Product attributes are fetching by schedule action, you can fetch product attributes manually after schedule action finish"
                },
            }

    @api.multi
    def auto_fetch_magento_data(self):
        """ Automatic Pull Data From Instance Follow Standard Process"""
        if not self.id:
            self = self.env['magento.backend'].search([], limit=1)

        # print('\n\n\n\n')
        # print("start fetch at " + str(datetime.datetime.now()))
        # time.sleep(120)
        # time.sleep(120)
        # print("start fetch at 1111 " + str(datetime.datetime.now()))

        # search and check if = false then run
        if not self.auto_fetching:
            print("start fetch at " + str(datetime.datetime.now()))
            self.env.cr.execute("""UPDATE magento_backend SET auto_fetching = TRUE WHERE id = %s""", (self.id,))
            self.env.cr.commit()
            try:
                print(1)
                self.fetch_products()
            except Exception as e:
                print('1' + str(e))
            try:
                print(3)
                self.fetch_customers()
            except Exception as e:
                print('3' + str(e))
            try:
                self.fetch_sale_orders()
            except Exception as e:
                print('4' + str(e))
            self.env.cr.execute("""UPDATE magento_backend SET auto_fetching = FALSE WHERE id = %s""", (self.id,))
            self.env.cr.commit()
            print("end fetch at " + str(datetime.datetime.now()))
