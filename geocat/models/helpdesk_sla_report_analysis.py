# -*- coding: utf-8 -*-
from odoo import fields, models

from .helpdesk_ticket import TICKET_PRIORITY  # , TICKET_CLASS


class HelpdeskSLAReport(models.Model):
    _inherit = 'helpdesk.sla.report.analysis'

    priority = fields.Selection(TICKET_PRIORITY, string='Minimum Priority', readonly=True)
    # classification = fields.Selection(TICKET_CLASS, string='Classification', readonly=True)
