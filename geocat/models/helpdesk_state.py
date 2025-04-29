from odoo import fields, models


class GeoCatHelpdeskState(models.Model):
    _name = 'geocat.helpdesk.state'
    _description = 'GeoCat Helpdesk Ticket Status'

    name = fields.Char(required=True)
    color = fields.Char(string='Primary Color', default='#c0c0c0', required=True)
    text_color = fields.Char(string='Text Color', default='#00000', required=True)
    stage_id = fields.Many2one('helpdesk.stage', string='Stage', required=True)

    def _update_ticket_model(self, reset_consolidated_statuses=False):
        ticket_model = self.env['helpdesk.ticket']
        if ticket_model is not None:
            # Make sure that all blocked states are loaded at start
            ticket_model.load_blocked_states()
            if reset_consolidated_statuses:
                # Make sure that the consolidates statuses of all tickets match the current states and stages
                ticket_model.reset_consolidated_statuses()

    def write(self, vals):
        """ Whenever a record is updated, we need to call helpdesk_ticket.load_blocked_states(). """
        res = super(GeoCatHelpdeskState, self).write(vals)
        # Update available states for ticket model and reset the consolidated statuses of all tickets
        self._update_ticket_model(reset_consolidated_statuses=True)
        return res

    def create(self, vals):
        """ Whenever a record is created, we need to call helpdesk_ticket.load_blocked_states(). """
        res = super(GeoCatHelpdeskState, self).create(vals)
        # For new records, we need to load the blocked states but do not have to reset the consolidated statuses
        self._update_ticket_model()
        return res

    def unlink(self):
        """ Whenever a record is deleted, we need to call helpdesk_ticket.load_blocked_states(). """
        res = super(GeoCatHelpdeskState, self).unlink()
        # Update available states for ticket model and reset the consolidated statuses of all tickets
        self._update_ticket_model(reset_consolidated_statuses=True)
        return res
