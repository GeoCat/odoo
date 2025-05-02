# -*- coding: utf-8 -*-
from re import compile
import logging

from odoo import models, api
from ..lib.utils import force_email_layout_xmlid_kwarg

_logger = logging.getLogger(__name__)

# Regex for WHMCS-style ticket references in mail message subjects
IMPORTED_TICKET_REF_RE = compile(r'\[Ticket ID: (\d{6})]')


class GeoCatMailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _notify_thread_by_email(self, message, recipients_data, msg_vals=False,
                                mail_auto_delete=True,  # mail.mail
                                model_description=False, force_email_company=False, force_email_lang=False,  # rendering
                                subtitles=None,  # rendering
                                resend_existing=False, force_send=True, send_after_commit=True,  # email send
                                **kwargs):
        """ Override to set the default email layout XML ID to a GeoCat one. """
        msg_vals = force_email_layout_xmlid_kwarg(msg_vals)
        return super()._notify_thread_by_email(message, recipients_data,
                                               msg_vals=msg_vals, mail_auto_delete=mail_auto_delete,
                                               model_description=model_description,
                                               force_email_company=force_email_company,
                                               force_email_lang=force_email_lang, subtitles=subtitles,
                                               resend_existing=resend_existing, force_send=force_send,
                                               send_after_commit=send_after_commit, **kwargs)

    @api.model
    def _message_route_process(self, message, message_dict, routes):
        """ Override to make sure that mail replies to old imported tickets to which the customer never replied before
        after the import do not trigger the creation of a new ticket, but instead will update the imported one.
        The reason that this could happen is that those replies will be missing the Odoo ticket reference headers
        in the email, so mail_thread cannot match the thread_id. Once we start replying to the customer, and they reply
        to those messages, the headers should appear and this problem will be resolved automatically.
        """
        processed_routes = []
        for model_name, thread_id, custom_values, user_id, alias in routes or ():
            if model_name != 'helpdesk.ticket' or thread_id:
                # If model is not helpdesk.ticket or thread_id is already set, handle the route normally
                processed_routes.append((model_name, thread_id, custom_values, user_id, alias))
                continue

            msg_subject = message_dict.get('subject', '')
            # Check if the subject contains an old WHMCS ticket reference (e.g. "[Ticket ID: 123456]")
            match = IMPORTED_TICKET_REF_RE.search(msg_subject)
            if not match:
                # No old ticket ref in subject: process as an actual new ticket
                processed_routes.append((model_name, thread_id, custom_values, user_id, alias))
                continue

            # Extract the old ticket reference number from the subject
            import_ref = match.group(1)
            _logger.info(f"Received message with legacy ticket reference '{import_ref}': trying to resolve matching ticket")
            # Find the ticket with the same reference
            model_object = self.env[model_name]
            if not hasattr(model_object, 'search') or 'import_ref' not in model_object._fields:
                # This should not happen, but we want to make sure that Odoo handles it normally
                _logger.warning(
                    f"Model '{model_name}' does not have a search method or import_ref field")
                processed_routes.append((model_name, thread_id, custom_values, user_id, alias))
                continue

            ticket = model_object.search([('import_ref', '=', import_ref)], limit=1)
            if ticket:
                _logger.info(f"Found existing ticket match with ID {ticket.id}: updating ticket")
                thread_id = ticket.id
            else:
                _logger.warning(f"Ticket with legacy reference '{import_ref}' not found: creating new ticket")
                if custom_values is None:
                    custom_values = {}
                custom_values['import_ref'] = import_ref
            processed_routes.append((model_name, thread_id, custom_values, user_id, alias))

        return super()._message_route_process(message, message_dict, processed_routes)
