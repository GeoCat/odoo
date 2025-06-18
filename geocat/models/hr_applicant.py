from odoo import models, api


class Applicant(models.Model):
    _inherit = 'hr.applicant'

    @api.returns('mail.message', lambda value: value.id)
    def message_notify(self, *,
                       body='', subject=False,
                       author_id=None, email_from=None,
                       model=False, res_id=False,
                       subtype_xmlid=None, subtype_id=False, partner_ids=False,
                       attachments=None, attachment_ids=None,
                       **kwargs):
        """ Override the message_notify method to customize the original email body for interviewer assignment, so we can add a link.
        NOTE: This is a bit of an ugly hack, but it is the only way to customize the email body, as the body is set to a string
        in the parent model's create/write methods, and there is no template defined or used anywhere.
        """

        expected_start = "You have been assigned as an interviewer"  # See Odoo 18 parent model create/write methods
        template_id = self.env['ir.model.data']._xmlid_to_res_id('geocat.hr_applicant_interviewer_assigned',
                                                                 raise_if_not_found=False)
        if body.startswith(expected_start) and template_id:
            # If the body starts with the expected string, we want to change it to a templated version
            if self:
                # Note that we expect to only handle one record at a time here
                self.ensure_one()
            values = {
                'job_position': self.job_id.display_name,
                'applicant_name': self.display_name,
                'access_link': self._notify_get_action_link('view'),
            }
            html = self.env['ir.qweb']._render('geocat.hr_applicant_interviewer_assigned', values,
                                               minimal_qcontext=True)
            body = self.env['mail.render.mixin']._replace_local_links(html)

        # Always return by calling the super method, even if we didn't change the body
        return super().message_notify(body=body, subject=subject, author_id=author_id, email_from=email_from,
                                      model=model, res_id=res_id, subtype_xmlid=subtype_xmlid, subtype_id=subtype_id,
                                      partner_ids=partner_ids, attachments=attachments, attachment_ids=attachment_ids,
                                      **kwargs)
