# -*- coding: utf-8 -*-
from odoo import http

# class AutoInstall(http.Controller):
#     @http.route('/auto_install/auto_install/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/auto_install/auto_install/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('auto_install.listing', {
#             'root': '/auto_install/auto_install',
#             'objects': http.request.env['auto_install.auto_install'].search([]),
#         })

#     @http.route('/auto_install/auto_install/objects/<model("auto_install.auto_install"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('auto_install.object', {
#             'object': obj
#         })