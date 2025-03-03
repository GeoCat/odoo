from odoo import models
from ..lib.utils import force_email_layout_xmlid_kwarg


class GeoCatMailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _notify_thread_by_email(self, message, recipients_data, msg_vals=False,
                                mail_auto_delete=True,  # mail.mail
                                model_description=False, force_email_company=False, force_email_lang=False,  # rendering
                                subtitles=None,  # rendering
                                resend_existing=False, force_send=True, send_after_commit=True,  # email send
                                **kwargs):
        """ Override to set the default email layout XML ID to a GeoCat one. """
        msg_vals = force_email_layout_xmlid_kwarg(msg_vals, self.env)
        return super()._notify_thread_by_email(message, recipients_data,
                                               msg_vals=msg_vals, mail_auto_delete=mail_auto_delete,
                                               model_description=model_description,
                                               force_email_company=force_email_company,
                                               force_email_lang=force_email_lang, subtitles=subtitles,
                                               resend_existing=resend_existing, force_send=force_send,
                                               send_after_commit=send_after_commit, **kwargs)
