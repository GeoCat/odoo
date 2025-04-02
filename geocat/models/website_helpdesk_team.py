# -*- coding: utf-8 -*-
from lxml import etree

from odoo import models


class HelpdeskTeam(models.Model):
    _inherit = 'helpdesk.team'

    def _combine_arch(self, base_arch, diff_arch):
        """ Combines a base architecture (QWeb XML) with a diff architecture (e.g. child XML).
        Returns the result as a new XML architecture string. """
        base_tree = etree.fromstring(base_arch)
        diff_tree = etree.fromstring(diff_arch)
        arch_node = self.env['ir.ui.view'].apply_inheritance_specs(base_tree, diff_tree)
        if not arch_node:
            return
        return etree.tostring(arch_node, pretty_print=True, encoding='unicode')

    # noinspection DuplicatedCode
    def _ensure_submit_form_view(self):
        teams = self.filtered('use_website_helpdesk_form')
        if not teams:
            return

        # Make sure that the derived helpdesk team form is updated according to the GeoCat default form
        odoo_arch = self.env.ref('website_helpdesk.ticket_submit_form').sudo().arch
        geocat_diff = self.env.ref('geocat.ticket_submit_form').sudo().arch
        geocat_arch = self._combine_arch(odoo_arch, geocat_diff) or odoo_arch
        for team in teams:
            xmlid = 'website_helpdesk.team_form_' + str(team.id)
            team_form = team.website_form_view_id

            if not team_form:
                # Create a new form view
                form_template = self.env['ir.ui.view'].sudo().create({
                    'type': 'qweb',
                    'arch': geocat_arch,
                    'name': xmlid,
                    'key': xmlid
                })
                # Create a new record for the form view
                self.env['ir.model.data'].sudo().create({
                    'module': 'website_helpdesk',
                    'name': xmlid.split('.')[1],
                    'model': 'ir.ui.view',
                    'res_id': form_template.id,
                    'noupdate': True
                })
                team.website_form_view_id = form_template.id

            elif team_form.xml_id == xmlid and team_form.arch != geocat_arch:
                # Force our own GeoCat form view on the existing form (if different)
                form_template = self.env['ir.ui.view'].sudo().search([('id', '=', team_form.id)], limit=1)
                if form_template:
                    # Update the arch of the existing form
                    form_template.write({'arch': geocat_arch})
