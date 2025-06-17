# -*- coding: utf-8 -*-
from lxml import etree

from odoo import models, fields, api


class HelpdeskTeam(models.Model):
    _inherit = ['helpdesk.team']

    # This field is looked up when a first reply is sent by internal users:
    # If not set, the stage is not changed. Otherwise, the stage is set to this value.
    # TODO?
    # goto_stage_on_first_reply = fields.Many2one('helpdesk.stage', string='Stage on First Reply',
    #                                             help='When a first response has been sent, you can automatically set '
    #                                                  'the ticket to a stage. Leave this empty to keep the stage as-is.',
    #                                             domain="[('id', 'in', stage_ids)]", ondelete='set null')

    # Taken from https://github.com/OCA/helpdesk/tree/18.0/helpdesk_mgmt_project
    default_project_id = fields.Many2one(
        comodel_name="project.project",
        string="Default Project",
        help="Fallback project for tickets that aren't associated with a customer project (yet).",
        readonly=False,
        ondelete='restrict',
    )
    default_task_id = fields.Many2one(
        string="Default Task",
        help="Fallback task for tickets that aren't associated with a customer task (yet).",
        comodel_name="project.task",
        compute="_compute_task_id",
        readonly=False,
        ondelete='restrict',
        store=True,
    )

    @api.depends("default_project_id")
    def _compute_task_id(self):
        # Taken from https://github.com/OCA/helpdesk/tree/18.0/helpdesk_mgmt_project
        for record in self:
            if record.default_task_id.project_id != record.default_project_id:
                record.default_task_id = False

    def _get_closing_stage(self):
        """ Override: try to find a stage with 'closed' in its name. """
        super_stage = super()._get_closing_stage()
        if len(super_stage) == 1:
            # No stage folding applied: super() returned the last stage
            return super_stage
        closing_stage = super_stage.filtered(lambda s: s.name.lower() == 'closed')
        if not closing_stage:
            # No stage name 'closed' found: return what super() found
            return super_stage
        # Return the first stage with the name 'closed'
        return closing_stage

    def _combine_arch(self, base_arch, diff_arch):
        """ Combines a base architecture (QWeb XML) with a diff architecture (e.g. child XML).
        Returns the result as a new XML architecture string. """
        base_tree = etree.fromstring(base_arch)
        diff_tree = etree.fromstring(diff_arch)
        arch_node = self.env['ir.ui.view'].apply_inheritance_specs(base_tree, diff_tree)
        if arch_node is None:
            return None
        return etree.tostring(arch_node, pretty_print=True, encoding='unicode')

    # noinspection DuplicatedCode
    def _ensure_submit_form_view(self):
        teams = self.filtered('use_website_helpdesk_form')
        if not teams:
            return

        # Make sure that the derived helpdesk team form is updated according to the GeoCat default form
        geocat_form = self.env.ref('geocat.ticket_submit_form', raise_if_not_found=False)
        if not geocat_form:
            # This could happen when the module is initialized: in this case, we will load the default form
            super()._ensure_submit_form_view()
            return

        odoo_arch = self.env.ref('website_helpdesk.ticket_submit_form').sudo().arch
        geocat_arch = geocat_form.sudo().arch
        combined_arch = self._combine_arch(odoo_arch, geocat_arch) or odoo_arch
        for team in teams:
            xmlid = 'website_helpdesk.team_form_' + str(team.id)
            team_form = team.website_form_view_id

            if not team_form:
                # Create a new form view
                form_template = self.env['ir.ui.view'].sudo().create({
                    'type': 'qweb',
                    'arch': combined_arch,
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

            elif team_form.xml_id == xmlid and team_form.arch != combined_arch:
                # Force our own GeoCat form view on the existing form (if different)
                form_template = self.env['ir.ui.view'].sudo().search([('id', '=', team_form.id)], limit=1)
                if form_template:
                    # Update the arch of the existing form
                    form_template.write({'arch': combined_arch})
