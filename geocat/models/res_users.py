# -*- coding: utf-8 -*-
from markupsafe import Markup

from odoo import api, models
from odoo.tools import is_html_empty


class Users(models.Model):
    """ Override to simply set the default user signature to the name wrapped in <p>."""
    _inherit = ['res.users']

    @api.depends('name')
    def _compute_signature(self):
        for user in self.filtered(lambda usr: usr.name and is_html_empty(user.signature)):
            user.signature = Markup('<p>%s</p>') % user['name']  # Omit the '--<br/>' that Odoo adds by default
