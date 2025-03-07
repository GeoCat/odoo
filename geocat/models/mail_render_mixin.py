# -*- coding: utf-8 -*-
from ..lib.utils import map_email_layout_template
from odoo import api, models


class MailRenderMixin(models.AbstractModel):
    _inherit = "mail.render.mixin"

    @api.model
    def _render_encapsulate(self, layout_xmlid, html, add_context=None, context_record=None):
        layout_xmlid = map_email_layout_template(layout_xmlid)  # Do not force a GeoCat layout (e.g. for digest mails we don't want that)
        return super()._render_encapsulate(layout_xmlid, html, add_context=add_context, context_record=context_record)
