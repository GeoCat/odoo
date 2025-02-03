# -*- coding: utf-8 -*-
from odoo import models


class MailTemplate(models.Model):
    _inherit = 'mail.template'

    def send_mail(self, *args, **kwargs):
        """ Override Odoo's send_mail method to set the default email layout XML ID if not set.
        Note that this means that we will have to remove all layout stuff (headers, footers) from the email template records!
        """
        if not kwargs.get('email_layout_xmlid'):
            # Set the default email layout XML ID if False or missing
            kwargs['email_layout_xmlid'] = 'mail.mail_notification_layout'

        return super(MailTemplate, self).send_mail(*args, **kwargs)
