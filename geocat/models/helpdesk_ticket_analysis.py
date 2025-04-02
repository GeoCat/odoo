# -*- coding: utf-8 -*-
from odoo import fields, models

from .helpdesk_ticket import TICKET_PRIORITY  # , TICKET_CLASS


class HelpdeskTicketReport(models.Model):
    _inherit = 'helpdesk.ticket.report.analysis'

    priority = fields.Selection(TICKET_PRIORITY, string='Minimum Priority', readonly=True)
    # classification = fields.Selection(TICKET_CLASS, string='Classification', readonly=True)  TODO: research what happens if we add this field
