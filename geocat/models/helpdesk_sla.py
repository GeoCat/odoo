# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from .helpdesk_ticket import TICKET_PRIORITY


class HelpdeskSLA(models.Model):
    _inherit = 'helpdesk.sla'

    priority = fields.Selection(TICKET_PRIORITY, string='Priority', default='1', required=True)

    @api.constrains('priority')
    def _check_priority(self):
        for sla in self:
            if sla.priority == '0':
                raise ValidationError(_("Priority 'Low' is excluded from GeoCat SLA Policies."))
