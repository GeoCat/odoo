# -*- coding: utf-8 -*-
from odoo import models, api
from ..lib.utils import force_email_layout_xmlid_kwarg


class MailTemplate(models.Model):
    _inherit = 'mail.template'

    @api.returns('self', lambda value: value.ids)
    def send_mail_batch(self, res_ids, **kwargs):
        """ Override to set the default email layout XML ID to a GeoCat one. """
        return super().send_mail_batch(res_ids, **force_email_layout_xmlid_kwarg(**kwargs))
