# -*- coding: utf-8 -*-
from odoo import models


class HelpdeskTeam(models.Model):
    _inherit = ['helpdesk.team']

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
