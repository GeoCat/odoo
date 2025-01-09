from odoo import models, fields


class Company(models.Model):
    """ Override that allows us to select Inter as the document layout font.
    Requires static/fonts/google/Inter TTF files and CSS include (geocat_fonts.scss) to work.
    """

    _inherit = 'res.company'

    font = fields.Selection(selection_add=[('Inter', 'Inter')])
