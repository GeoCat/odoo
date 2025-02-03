# -*- coding: utf-8 -*-
from odoo import models


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    def _prepare_mail_values_static(self):
        """ Override Odoo's _prepare_mail_values method to set the default email layout XML ID if not set.
        Note that this means that we will have to remove all layout stuff (headers, footers) from the email template records!
        """
        values = super(MailComposer, self)._prepare_mail_values_static()
        if not values.get('email_layout_xmlid'):
            # Set the default email layout XML ID if False or missing
            values['email_layout_xmlid'] = 'mail.mail_notification_layout'
        return values
