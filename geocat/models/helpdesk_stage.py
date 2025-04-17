# -*- coding: utf-8 -*-
from odoo import fields, models


class HelpdeskStage(models.Model):
    _inherit = 'helpdesk.stage'

    color = fields.Char(required=True, default='#000000', string='Text Color',
                        help="Foreground color associated with this stage. Used for the text in the consolidated status badge in the helpdesk portal.")
    bgcolor = fields.Char(required=True, default='#c0c0c0', string='Background Color', help="Background color associated with this stage. Used for the consolidated status badge in the helpdesk portal.")
