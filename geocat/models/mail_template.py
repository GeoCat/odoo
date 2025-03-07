# -*- coding: utf-8 -*-
from odoo import models, api
from ..lib.utils import map_email_layout_template


class MailTemplate(models.Model):
    _inherit = 'mail.template'

    @api.returns('self', lambda value: value.ids)
    def send_mail_batch(self, res_ids, force_send=False, raise_exception=False, email_values=None, email_layout_xmlid=False):
        """ Override to set the default email layout XML ID to a GeoCat one. """
        return super().send_mail_batch(res_ids, force_send=force_send,
                                       raise_exception=raise_exception, email_values=email_values,
                                       email_layout_xmlid=map_email_layout_template(email_layout_xmlid, True))
