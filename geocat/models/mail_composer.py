# -*- coding: utf-8 -*-
from odoo import models
from ..lib.utils import force_email_layout_xmlid_kwarg


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    def _prepare_mail_values_static(self):
        """ Override Odoo's _prepare_mail_values method to set the default email layout XML ID to a GeoCat one.
        Note that this means that we will have to remove all layout-related stuff (headers, footers) from the standard
        Odoo email template records, else we may get multiple headers/footers in the email.
        """
        values = super(MailComposer, self)._prepare_mail_values_static()
        return force_email_layout_xmlid_kwarg(values)
