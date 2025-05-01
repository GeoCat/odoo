# -*- coding: utf-8 -*-
from re import compile

from odoo import api, fields, models
from odoo.addons.helpdesk.models.helpdesk_ticket import HelpdeskTicket as BaseHelpdeskTicket

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

# Regex for WHMCS-style ticket references in email subjects
IMPORTED_TICKET_REF_RE = compile(r'\[Ticket ID: (\d{6})]')

# Global variable to store all blocked states:
# these are populated from the geocat.helpdesk.state model (see load_blocked_states())
_all_blocked_states = {}


class HelpdeskTicket(models.Model):
    """ Override that permanently adds our GeoCat ticket classifications along with some BL. """

    _description = 'GeoCat Helpdesk Ticket'
    _inherit = ['helpdesk.ticket']

    priority = fields.Selection(TICKET_PRIORITY, compute='_compute_priority', store=True, default='0', tracking=True)
    classification = fields.Selection(TICKET_CLASS, string='Classification', required=True, default=UNKNOWN_CLASS, tracking=True)
    blocked_state = fields.Many2one(
        'geocat.helpdesk.state',
        string='Blocked State',
        domain="[('stage_id', '=', stage_id)]",
        tracking=True, ondelete='set null',
        groups='helpdesk.group_helpdesk_user'
    )
    consolidated_color = fields.Char(string='Text Color', compute='_compute_consolidated_color', store=False, readonly=True)
    consolidated_bgcolor = fields.Char(string='Background Color', compute='_compute_consolidated_bgcolor', store=False, readonly=True)
    consolidated_status = fields.Char(string='Ticket Status', compute='_compute_consolidated_status', store=True, readonly=True)
    all_blocked_states_json = fields.Json(
        compute='_compute_all_blocked_states',
        copy=False, store=False
    )

    # The following field stores the original WHMCS ticket reference if it was imported:
    # this is used in the display name when present, and also looked up in the message_new() method (if user emails)
    import_ref = fields.Char(string='Imported Ticket Reference', readonly=True, index='btree_not_null')

    @api.depends('ticket_ref', 'import_ref', 'partner_name')
    @api.depends_context('with_partner')
    def _compute_display_name(self):
        display_partner_name = self._context.get('with_partner', False)
        ticket_with_name = self.filtered('name')
        for ticket in ticket_with_name:
            name = ticket.name
            if ticket.import_ref:
                name += f' (#{ticket.import_ref})'
            elif ticket.ticket_ref:
                name += f' (#{ticket.ticket_ref})'
            if display_partner_name and ticket.partner_name:
                name += f' - {ticket.partner_name}'
            ticket.display_name = name
        # We want to skip the display name computation of the inherited ticket class completely,
        # so we call super() on the base class (BaseModel) instead of the inherited class.
        return super(BaseHelpdeskTicket, self - ticket_with_name)._compute_display_name()

    def _set_blocked_states_for_stage(self):
        for ticket in self:
            if not ticket.stage_id or not _all_blocked_states:
                ticket.all_blocked_states_json = []
                continue
            # Get the blocked states for the current stage
            blocked_states = _all_blocked_states.get(ticket.stage_id.id, [])
            ticket.all_blocked_states_json = blocked_states

    @api.depends('stage_id')
    def _compute_all_blocked_states(self):
        self._set_blocked_states_for_stage()

    @api.onchange('stage_id')
    def _reset_ticket_state(self):
        """ Clear the selected state when the stage changes. """
        self.blocked_state = False

    def init(self):
        # Make sure that the classification field is always available in the form builder
        self.env['ir.model.fields'].formbuilder_whitelist('helpdesk.ticket', ['classification'])

        # Ensure that the helpdesk form view is available and up-to-date (for all teams, but we only have one)
        teams = self.env['helpdesk.team'].search([('use_website_helpdesk_form', '=', True)])
        teams._ensure_submit_form_view()

        # Load all blocked states from the geocat.helpdesk.state model (should have been initialized first)
        self.load_blocked_states()

        # Make sure that all statuses are up-to-date
        self.reset_consolidated_statuses()

    @api.model
    def load_blocked_states(self):
        """ (Re)load all blocked states. There should only be a few, so no real performance or memory hit. """
        global _all_blocked_states
        _all_blocked_states = {}
        states = self.env['geocat.helpdesk.state'].search([])
        for state in states:
            stage = _all_blocked_states.setdefault(state.stage_id.id, [])
            stage.append({
                'id': state.id,
                'name': state.name,
                'color': state.color,
                'stage_id': state.stage_id.id,
            })

    @api.model
    def reset_consolidated_statuses(self):
        """ Reset the consolidated status for all tickets. As this is a potentially heavy operation,
        only call this at startup or when states or stages are modified by an administrator. """
        self.search([])._compute_consolidated_status()

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

    @api.depends('stage_id', 'blocked_state')
    def _compute_consolidated_color(self):
        """ Compute the consolidated color based on stage and blocked state. Mostly required for portal users. """
        for ticket in self:
            ticket.consolidated_color = ticket.stage_id.color
            if ticket.blocked_state:
                ticket.consolidated_color = ticket.blocked_state.text_color

    @api.depends('stage_id', 'blocked_state')
    def _compute_consolidated_bgcolor(self):
        """ Compute the consolidated background color based on stage and blocked state. Mostly required for portal users. """
        for ticket in self:
            ticket.consolidated_bgcolor = ticket.stage_id.bgcolor
            if ticket.blocked_state:
                ticket.consolidated_bgcolor = ticket.blocked_state.color

    @api.depends('stage_id', 'blocked_state')
    def _compute_consolidated_status(self):
        """ Compute the consolidated status based on stage and blocked state. Mostly required for portal users. """
        for ticket in self:
            ticket.consolidated_status = ticket.stage_id.name
            if ticket.blocked_state:
                ticket.consolidated_status = ticket.blocked_state.name

    @api.model
    def message_new(self, msg, custom_values=None):
        """ Override of the regular message_new method to make sure that mail replies to old imported tickets
        to which the customer never replied before after the import do not trigger the creation of a new ticket,
        but instead will update the imported one. The reason that this could happen is that those replies
        will be missing the Odoo ticket reference headers in the email, so mail_thread cannot match the thread_id.
        Once we start replying to the customer, the headers should appear and this problem will be resolved automatically.
        """

        msg_subject = msg.get('subject', '')
        # Check if the subject contains an old WHMCS ticket reference (e.g. "[Ticket ID: 123456]")
        match = IMPORTED_TICKET_REF_RE.match(msg_subject)
        if match:
            # Extract the old ticket reference number from the subject
            import_ref = match.group(1)
            # Find the ticket with the same reference
            ticket = self.search([('import_ref', '=', import_ref)], limit=1)
            if ticket:
                # Now call message_update() instead to avoid creating a new ticket
                ticket.message_update(msg)
                # Make sure to return the ticket object, as this is what the caller expects
                return ticket

        # No old ticket ref (or never imported): process as an actual new ticket
        return super(HelpdeskTicket, self).message_new(msg, custom_values=custom_values)
