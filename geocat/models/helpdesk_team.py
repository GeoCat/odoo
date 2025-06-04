# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HelpdeskTeam(models.Model):
    _inherit = ['helpdesk.team']

    # This field is looked up when a first reply is sent by internal users:
    # If not set, the stage is not changed. Otherwise, the stage is set to this value.
    # TODO?
    # goto_stage_on_first_reply = fields.Many2one('helpdesk.stage', string='Stage on First Reply',
    #                                             help='When a first response has been sent, you can automatically set '
    #                                                  'the ticket to a stage. Leave this empty to keep the stage as-is.',
    #                                             domain="[('id', 'in', stage_ids)]", ondelete='set null')

    # Taken from https://github.com/OCA/helpdesk/tree/18.0/helpdesk_mgmt_project
    default_project_id = fields.Many2one(
        comodel_name="project.project",
        string="Default Project",
        help="Fallback project for tickets that aren't associated with a customer project (yet).",
        readonly=False,
        ondelete='restrict',
    )
    default_task_id = fields.Many2one(
        string="Default Task",
        help="Fallback task for tickets that aren't associated with a customer task (yet).",
        comodel_name="project.task",
        compute="_compute_task_id",
        readonly=False,
        ondelete='restrict',
        store=True,
    )

    @api.depends("default_project_id")
    def _compute_task_id(self):
        # Taken from https://github.com/OCA/helpdesk/tree/18.0/helpdesk_mgmt_project
        for record in self:
            if record.default_task_id.project_id != record.default_project_id:
                record.default_task_id = False

    def _get_closing_stage(self):
        """ Override: try to find a stage with 'closed' in its name. """
        super_stage = super()._get_closing_stage()
        if len(super_stage) == 1:
            # No stage folding applied: super() returned the last stage
            return super_stage
        closing_stage = super_stage.filtered(lambda s: s.name.lower() == 'closed')
        if not closing_stage:
            # No stage name 'closed' found: return what super() found
            return super_stage
        # Return the first stage with the name 'closed'
        return closing_stage
