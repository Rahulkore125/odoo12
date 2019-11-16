# -*- coding: utf-8 -*-
{
    'name': "advanced_sale",

    'summary': """Update flow sale for flow of Drinkies""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '1.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'delivery', 'mail', 'website_sale_coupon', 'stock', 'sales_team'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/sale_team_heineken_data.xml',
        'views/res_partner_view.xml',
        'views/sale_order_view.xml',
        'views/sale_hnk_report_view.xml'
    ],
}