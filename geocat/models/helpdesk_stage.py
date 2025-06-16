# -*- coding: utf-8 -*-
from odoo import fields, models


class GeoCatHelpdeskStage(models.Model):
    _inherit = 'helpdesk.stage'

    name = fields.Char(required=True, translate=False)  # Do not translate stage names in the database (just like status)
    color = fields.Char(required=True, default='#000000', string='Text Color',
                        help="Foreground color associated with this stage. Used for the text in the consolidated status badge in the helpdesk portal.")
    bgcolor = fields.Char(required=True, default='#c0c0c0', string='Background Color', help="Background color associated with this stage. Used for the consolidated status badge in the helpdesk portal.")

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

    def unlink(self):
        """ Whenever a record is deleted, we need to recompute the consolidated status. """
        res = super(GeoCatHelpdeskStage, self).unlink()
        self._update_consolidated_status()
        return res
