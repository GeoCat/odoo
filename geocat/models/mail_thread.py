from odoo import models
from ..lib.utils import force_email_layout_xmlid_kwarg


class GeoCatMailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _notify_thread_by_email(self, message, recipients_data, **kwargs):
        """ Override to set the default email layout XML ID to a GeoCat one. """
        return super()._notify_thread_by_email(message, recipients_data, **force_email_layout_xmlid_kwarg(**kwargs))
