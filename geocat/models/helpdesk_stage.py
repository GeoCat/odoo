# -*- coding: utf-8 -*-
from odoo import fields, models, api


class GeoCatHelpdeskStage(models.Model):
    _inherit = 'helpdesk.stage'

    name = fields.Char(required=True, translate=False)  # Do not translate stage names in the database (just like status)
    color = fields.Char(required=True, default='#000000', string='Text Color',
                        help="Foreground color associated with this stage. Used for the text in the consolidated status badge in the helpdesk portal.")
    bgcolor = fields.Char(required=True, default='#c0c0c0', string='Background Color', help="Background color associated with this stage. Used for the consolidated status badge in the helpdesk portal.")

    @api.model
    def _update_consolidated_status(self):
        ticket_model = self.env['helpdesk.ticket']
        if ticket_model is not None:
            # Make sure that the consolidates statuses of all tickets match the current states and stages
            ticket_model._reset_consolidated_statuses()

    def write(self, vals):
        """ Whenever a stage is updated (e.g. renamed), we need to recompute the consolidated status. """
        res = super(GeoCatHelpdeskStage, self).write(vals)
        self._update_consolidated_status()
        return res

    # NOTE: We do not need to override unlink() or create() here:
    # - Deleting a stage is not allowed if there are tickets in that stage,
    #   so a user would have to set them to another stage first,
    #   which would trigger the consolidated status to be recomputed anyway.
    # - New stages will only require a recomputation of the consolidated status
    #   if tickets are set to that stage (which triggers the recomputation).