# -*- coding: utf-8 -*-
from functools import lru_cache

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


class HelpdeskTicket(models.Model):
    """ Override that permanently adds our GeoCat ticket classifications along with some BL. """

    _description = 'Ticket'  # Note: this is used in buttons and other UI elements, e.g. "View %description%"
    _inherit = ['helpdesk.ticket']

    applies_to = fields.Char(string='Applies to', tracking=True,
                             help='Specifies the software and/or version that a ticket applies to.')
    priority = fields.Selection(TICKET_PRIORITY, compute='_compute_priority', store=True, default='0', tracking=True)
    classification = fields.Selection(TICKET_CLASS, string='Classification', required=True, default=UNKNOWN_CLASS,
                                      tracking=True, index=True,
                                      help='Classification of the ticket, used to determine the priority and SLA.'
                                           '"P"-tickets count towards the SLA and have a priority associated with them.')
    blocked_state = fields.Many2one(
        'geocat.helpdesk.state',
        string='Blocked State', domain="[('stage_id', '=', stage_id)]", readonly=False,
        tracking=True, ondelete='set null', index=True,
    )
    consolidated_color = fields.Char(string='Text Color', compute='_compute_consolidated_color', store=False,
                                     readonly=True)
    consolidated_bgcolor = fields.Char(string='Background Color', compute='_compute_consolidated_bgcolor', store=False,
                                       readonly=True)
    consolidated_status = fields.Char(string='Ticket Status', compute='_compute_consolidated_status', store=True,
                                      readonly=True)
    all_blocked_states_json = fields.Json(
        compute='_compute_all_blocked_states', compute_sudo=True,
        copy=False, store=False
    )

    # The following field stores the original WHMCS 6-digit ticket reference if it was imported:
    # this is used in the display name (if present), and is also looked up in the message_new() method (if email was received).
    # Note that we do not allow to set this field anywhere, except when the field is explicitly imported during create().
    import_ref = fields.Char(string='Imported Ticket Reference', readonly=True, index='btree_not_null',
                             help='Legacy ticket reference (from WHMCS import)')
    # The display_ref field is used to show the ticket reference in the UI (based on the import_ref or ticket_ref).
    display_ref = fields.Char(string='Ticket ID', compute='_compute_display_ref', store=True, readonly=True,
                              index=True)

    # This field can be used to store the date when the ticket was originally created (e.g. in WHMCS).
    # The value may be explicitly set during create(). If omitted, the create_date will be used.
    ticket_date = fields.Datetime(string='Ticket Date', help='Date when the ticket was originally created.', index=True)

    # This field can be used to store the user that originally reported the ticket (e.g. in WHMCS).
    # The value may be explicitly set during create(). If omitted, the create_uid will be used.
    reporter_id = fields.Many2one('res.users', string='Reported by', copy=True, index=True)

    # The following fields are used to link the ticket to a project and task.
    # This is taken from https://github.com/OCA/helpdesk/tree/18.0/helpdesk_mgmt_project
    project_id = fields.Many2one('project.project', string='Project', tracking=True, index=True,
                                 help='Project to which this ticket is linked (e.g. for time tracking). Defaults to team project for new tickets.',
                                 domain="[('partner_id', '=', commercial_partner_id.id)]", copy=True)
    task_id = fields.Many2one('project.task', string='Task', compute='_compute_task_id', store=True,
                              help='Project task for time tracking. Defaults to team task for new tickets.', index=True,
                              tracking=True, readonly=False, copy=True)
    default_project_id = fields.Many2one(related='team_id.default_project_id')

    @api.depends('project_id', 'team_id.default_project_id')
    def _compute_task_id(self):
        # Inspired by https://github.com/OCA/helpdesk/tree/18.0/helpdesk_mgmt_project
        for record in self:
            if record.task_id.project_id == record.project_id:
                # If the task is already linked to the correct project, do nothing
                continue

            if record.project_id and record.project_id == record.team_id.default_project_id:
                # If the project is the default project of the team, set the task to the default task
                record.task_id = record.team_id.default_task_id or False
            else:
                record.task_id = False

    @api.depends('import_ref', 'ticket_ref')
    def _compute_display_ref(self):
        """ Compute the display reference based on the ticket_ref and import_ref fields. """
        for ticket in self:
            ticket.display_ref = ticket.import_ref or ticket.ticket_ref or False

    @api.depends('display_ref', 'partner_name')
    @api.depends_context('with_partner')
    def _compute_display_name(self):
        display_partner_name = self._context.get('with_partner', False)
        ticket_with_name = self.filtered('name')
        for ticket in ticket_with_name:
            name = f'{ticket.name} (#{ticket.display_ref})'
            if display_partner_name and ticket.partner_name:
                name += f' - {ticket.partner_name}'
            ticket.display_name = name
        # We want to skip the display name computation of the inherited ticket class completely,
        # so we call super() on the base class (BaseModel) instead of the inherited class.
        return super(BaseHelpdeskTicket, self - ticket_with_name)._compute_display_name()

    @lru_cache(maxsize=16)
    @api.model
    def _blocked_states_for_stage(self, stage) -> list[dict]:
        state_records = self.env['geocat.helpdesk.state'].sudo().search([('stage_id', '=', stage.id)])
        state_objects = []
        for state in state_records:
            state_objects.append({
                'id': state.id,
                'name': state.name,
                'color': state.color,
                'stage_id': state.stage_id.id,
            })
        return state_objects

    def _set_blocked_states_for_stage(self):
        for ticket in self:
            if not ticket.stage_id:
                ticket.all_blocked_states_json = []
                continue
            # Get the blocked states for the current stage
            stage_states = self._blocked_states_for_stage(ticket.stage_id)
            ticket.all_blocked_states_json = stage_states

    @api.depends('stage_id')
    def _compute_all_blocked_states(self):
        self._set_blocked_states_for_stage()

    @api.onchange('stage_id')
    def _reset_ticket_state(self):
        """ Clear the selected state when the stage changes. """
        self.blocked_state = False

    def init(self):
        """ Initialize the helpdesk ticket model with the required fields and data."""

        # Use savepoint to prevent concurrent modifications from causing issues
        with self.env.cr.savepoint():
            # Make sure that the classification field is always available in the form builder
            self.env['ir.model.fields'].formbuilder_whitelist('helpdesk.ticket', ['classification'])

            # Make sure that the ticket_date and reported_id fields are set on all existing tickets
            self.env.cr.execute("""
                                UPDATE helpdesk_ticket
                                SET reporter_id = create_uid, ticket_date = create_date
                                WHERE reporter_id IS NULL AND ticket_date IS NULL
                                """)

        # Ensure that the helpdesk form view is available and up-to-date (for all teams, but we only have one)
        teams = self.env['helpdesk.team'].search([('use_website_helpdesk_form', '=', True)])
        teams._ensure_submit_form_view()

        # Make sure that all statuses are up-to-date
        self._reset_consolidated_statuses()

    @api.model
    def _reset_blocked_states(self):
        """ Clears blocked states cache. """
        if hasattr(self._blocked_states_for_stage, 'clear_cache'):
            self._blocked_states_for_stage.clear_cache()

    @api.model
    def _reset_consolidated_statuses(self):
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

    def _track_template(self, changes):
        """ Override to prevent sending notifications when moving the ticket back to the 'New' stage.
        The write() override makes sure that the 'mail_auto_subscribe_no_notify' context is set.
        """
        res = super()._track_template(changes)
        if 'stage_id' in res and self.env.context.get('dont_notify', False) and self.stage_id.sequence == 0:
            # Do NOT send a notification based on the stage's email template if we set the ticket (back) to the 'New' stage ourselves!
            del res['stage_id']
        return res

    @api.model
    def default_get(self, fields_list):
        """ Override to set the default project and task based on the team. """
        defaults = super().default_get(fields_list)

        if self.env.user.has_group('base.group_user'):
            # For internal users, we do not want to set the 'New' stage (sequence=0),
            # but the 'In Progress' stage (sequence=1). 'New' is only meant for tickets reported by portal users.
            in_progress_stage = self.env['helpdesk.stage'].search([('sequence', '=', 1)], limit=1)
            if in_progress_stage:
                defaults['stage_id'] = in_progress_stage.id

        return defaults

    def write(self, vals):
        """ Override to make sure that no notifications are being sent if we move the ticket BACK to "New" stage.
        Also, when the commercial partner changes and we (GeoCat) are doing that, we want to:
            - clear all followers that belong to the old partner
            - add all portal users linked to the new partner as followers
        """
        if self.env.user._is_internal():
            # The following logic should only be applied if the user is internal (i.e. a GeoCat employee)
            new_partner_id = vals.get('partner_id')
            if new_partner_id is not None:
                # Always remove the followers linked to the old/current partner (=customer)
                old_partner_id = self.commercial_partner_id.id
                if old_partner_id:
                    self.message_unsubscribe(partner_ids=self.message_partner_ids.filtered(lambda p: p.commercial_partner_id.id == old_partner_id).ids)

                if new_partner_id:
                    # Only if a new partner is set (i.e. not False), we want to add ALL portal users linked to the new partner as followers.
                    # Note that if no portal users have been configured for the new partner, no one will be subscribed.
                    portal_users = self.env['res.users'].search([
                        ('partner_id', 'child_of', self.env['res.partner'].browse(new_partner_id).commercial_partner_id.id),
                        ('groups_id', 'in', self.env.ref('base.group_portal').id)
                    ])
                    new_partner_ids = set(portal_users.mapped('partner_id').ids) - set(self.message_partner_ids.ids)
                    if new_partner_ids:
                        self.message_subscribe(partner_ids=list(new_partner_ids))

            new_user_id = vals.get('user_id')
            if new_user_id is not None:  # NOTE: if user_id was unset, new_user_id will be False!
                # If the user_id (assignee) has changed, we want to unsubscribe the old user and subscribe the new assignee (unless the old user is the creator)
                old_user_id = self.user_id.id
                if old_user_id and old_user_id != self.create_uid.id:
                    self.message_unsubscribe(partner_ids=self.message_partner_ids.filtered(lambda p: p.user_id.id == old_user_id).ids)

                if new_user_id:
                    # If the new user is set (i.e. not False), we want to subscribe the new assignee.
                    # This should already happen automatically, but just in case, we do it explicitly here.
                    new_partner_id = self.env['res.users'].browse(new_user_id).partner_id
                    if new_partner_id and set(self.message_partner_ids.ids).isdisjoint(new_partner_id.ids):
                        self.message_subscribe(partner_ids=new_partner_id.ids)

        if 'stage_id' in vals and self.stage_id.sequence > 0:
            # If we are moving the ticket BACK to the 'New' stage (sequence=0), e.g. when coming from "In Progress",
            # we do NOT want Odoo to send the "Helpdesk: Ticket Received" notification!
            new_stage = self.env['helpdesk.stage'].browse(vals['stage_id'])
            if new_stage and new_stage.sequence == 0:
                self = self.with_context(dont_notify=True)

        # Call super to perform the actual write operation
        return super(HelpdeskTicket, self).write(vals)

    @api.model_create_multi
    def create(self, list_value):
        """ Override that sets the ticket date to the current date if not set.
        Also makes sure that we do not immediately notify the customer if WE created the ticket on their behalf,
        and that we subscribe all portal users linked to the customer.
        """
        custom_notify = self.env.user._is_internal()

        # When GeoCat creates a ticket, we don't want to send the "Helpdesk: Ticket Received" notification
        tickets = super(HelpdeskTicket, self.with_context(dont_notify=custom_notify)).create(list_value)

        for ticket in tickets:
            # Set the ticket_date and reporter_id to the create_date and create_uid respectively if not set
            ticket.ticket_date = ticket.ticket_date or ticket.create_date
            ticket.reporter_id = ticket.reporter_id or ticket.create_uid

            if not custom_notify:
                # Customer or system created the ticket: super() has already sent default stage notification(s)
                continue

            # The call to super() should have subscribed the ticket creator, assignee (user_id) and the customer (partner_id).
            # However, we also want to subscribe any portal users linked to the customer, otherwise only the main customer address will get notified.
            if ticket.partner_id:
                # Only if a partner is set (i.e. not False), we want to add ALL portal users linked to the partner as followers.
                # Note that if NO portal users have been configured for the partner, no (additional) partners will be subscribed.
                portal_users = self.env['res.users'].search([
                    ('partner_id', 'child_of', self.env['res.partner'].browse(ticket.partner_id.id).commercial_partner_id.id),
                    ('groups_id', 'in', self.env.ref('base.group_portal').id)
                ])
                new_partner_ids = set(portal_users.mapped('partner_id').ids) - set(ticket.message_partner_ids.ids)
                if new_partner_ids:
                    ticket.message_subscribe(partner_ids=list(new_partner_ids))

            # Send a message to partner(s) if the ticket has a description, name and following partners
            if ticket.description and ticket.name and ticket.message_partner_ids:
                # Note: the message_type is "notification" by default:
                #       This means that the customer will get an email, but will not see the message in the portal.
                #       However, they will see the description in the ticket details of course.
                #       Also, the message will be visible in the internal Chatter, but will look like a Note.
                ticket.message_post(
                    body=ticket.description,
                    subject=ticket.name,
                    subtype_xmlid='mail.mt_comment',
                    partner_ids=ticket.message_partner_ids.ids,
                )

        return tickets

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, *args, body='', message_type='notification', **kwargs):
        """ Override that wraps our replies in a layout with a button to access the ticket in the portal.
        Also puts the ticket in the next stage (with sequence=1) if we are posting the first message.
        """
        kwargs['email_layout_xmlid'] = 'geocat.mail_layout_light_button_access'
        message = super().message_post(*args, body=body, message_type=message_type, **kwargs)

        # NOTE: message_post() super is called on a single record (ensure_one()) so we can safely use self now.
        #       It should have set the answered_customer_message_count to 1, if this was a first reply.

        # Check if the message is sent to the customer (not an internal note)
        if kwargs.get('subtype_xmlid') == 'mail.mt_comment':
            # ... and set the ticket to 'In Progress' stage if this is the first reply
            self._update_stage_on_first_reply()

        return message

    def _update_stage_on_first_reply(self):
        """ Sets ticket to 'In Progress' stage if this is the first reply and the ticket is in 'New' stage. """
        self.ensure_one()
        if self.stage_id.sequence == 0 and self.answered_customer_message_count == 1:
            # If the ticket is in the 'New' stage and the first reply was posted, set it to 'In Progress'
            in_progress_stage = self.env['helpdesk.stage'].search([('sequence', '=', 1)], limit=1)
            if in_progress_stage:
                self.stage_id = in_progress_stage

    def _send_email_notify_to_cc(self, partners_to_notify):
        """ Override that does nothing, so users will not receive the 'You are invited to follow ...' message.
        The reason we do this is that these notifications are quite superfluous and not very useful.
        """
        pass

    def _message_auto_subscribe_notify(self, partner_ids, template):
        """ Override to make sure that we are using our own assignment notification template that is actually USEFUL,
        because it includes a link to the ticket (Odoo's default template does not).
        """
        if template == 'mail.message_user_assigned':
            template = 'geocat.helpdesk_ticket_message_user_assigned'
        super()._message_auto_subscribe_notify(partner_ids, template)
