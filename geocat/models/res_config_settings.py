# -*- coding: utf-8 -*-
from odoo import _, models
from odoo.exceptions import UserError
from ..lib.utils import map_email_layout_template


class ResConfigSettings(models.TransientModel):
    """ Override of Odoo mail config model so that the 'Update Mail Layout' button
        refers to the GeoCat master email layout template. """
    _inherit = 'res.config.settings'

    def open_email_layout(self):
        return_value = super().open_email_layout()
        if not isinstance(return_value, dict) or 'res_id' not in return_value:
            # Unexpected: we cannot override the res_id if it's missing
            return return_value

        layout_name = map_email_layout_template('mail.mail_notification_layout', True)
        layout = self.env.ref(layout_name, raise_if_not_found=False)
        if not layout:
            raise UserError(_("This layout seems to no longer exist."))
        return_value['res_id'] = layout.id
        return return_value
