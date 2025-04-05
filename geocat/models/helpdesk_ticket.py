# -*- coding: utf-8 -*-
from odoo import api, fields, models

UNKNOWN_CLASS = 'X1'
DEFAULT_CLASS = 'P3'
TICKET_CLASS = [
    ('P1', 'Immediate (P1)'),
    ('P2', 'Urgent (P2)'),
    (DEFAULT_CLASS, f'Normal ({DEFAULT_CLASS})'),
    ('S1', 'Application Management (S1)'),
    ('S2', 'User Support (S2)'),
    ('S3', 'Change Request (S3)'),
    (UNKNOWN_CLASS, f'Unclassified ({UNKNOWN_CLASS})'),
]

# NOTE: We override the labels of the Odoo priority field to match the GeoCat classification.
# This means that we'll have to override all usages of TICKET_PRIORITY in other helpdesk models as well!
TICKET_PRIORITY = [
    ('0', 'Low'),
    ('1', 'Normal'),
    ('2', 'Urgent'),
    ('3', 'Immediate'),
]


class HelpdeskTicket(models.Model):
    """ Override that permanently adds our GeoCat ticket classifications along with some BL. """

    _description = 'GeoCat Helpdesk Ticket'
    _inherit = ['helpdesk.ticket']

    priority = fields.Selection(TICKET_PRIORITY, compute='_compute_priority', store=True, default='0', tracking=True)
    classification = fields.Selection(TICKET_CLASS, string='Classification', required=True, default=UNKNOWN_CLASS, tracking=True)

    def init(self):
        self.env['ir.model.fields'].formbuilder_whitelist('helpdesk.ticket', ['classification'])

    @staticmethod
    def _class_to_priority(classification):
        """ Maps GeoCat classification to Odoo priority (0-3).
        Classifications without the 'P' prefix will return priority 0.
        """
        return {
            'P1': '3',
            'P2': '2',
            'P3': '1',
        }.get(classification, '0')

    @api.depends('classification')
    def _compute_priority(self):
        """ Updates the Odoo priority if the GeoCat classification changes. """
        for ticket in self:
            ticket.priority = self._class_to_priority(ticket.classification)

    @api.model
    def _sla_reset_trigger(self):
        # Make sure that a changed classification also triggers an SLA reset
        field_list = super()._sla_reset_trigger()
        field_list.append('classification')
        return field_list
