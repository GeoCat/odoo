from odoo import fields, models


class GeoCatHelpdeskState(models.Model):
    _name = 'geocat.helpdesk.state'
    _description = 'GeoCat Helpdesk Ticket Status'

    name = fields.Char(required=True)
    color = fields.Char(string='Primary Color', default='#c0c0c0', required=True)
    text_color = fields.Char(string='Text Color', default='#00000', required=True)
    stage_id = fields.Many2one('helpdesk.stage', string='Stage', required=True)

    def init(self):
        # Make sure that all blocked states are loaded at start
        self.env['helpdesk.ticket'].load_blocked_states()

    def write(self, vals):
        """ Whenever a record is added or updated, we need to call helpdesk_ticket.load_blocked_states """
        res = super(GeoCatHelpdeskState, self).write(vals)
        self.env['helpdesk.ticket'].load_blocked_states()
        return res
