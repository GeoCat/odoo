# -*- coding: utf-8 -*-
from odoo import models, fields


class HelpdeskTeam(models.Model):
    _inherit = ['helpdesk.team']

    # This field is looked up when a first reply is sent by internal users:
    # If not set, the stage is not changed. Otherwise, the stage is set to this value.
    # TODO?
    # goto_stage_on_first_reply = fields.Many2one('helpdesk.stage', string='Stage on First Reply',
    #                                             help='When a first response has been sent, you can automatically set '
    #                                                  'the ticket to a stage. Leave this empty to keep the stage as-is.',
    #                                             domain="[('id', 'in', stage_ids)]", ondelete='set null')

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
