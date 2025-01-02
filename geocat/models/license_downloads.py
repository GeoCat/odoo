from odoo import fields, models, api


class GeoCatBridgeLicenseDownload(models.Model):

    _name = 'geocat.license.downloads'
    _table = 'geocat_license_downloads'
    _description = 'License File Downloads'
    _order = 'customer_name asc, write_date desc'

    # === FIELD DEFINITIONS ===
    license_id = fields.Many2one('geocat.license.keys', string='License Key', required=True, ondelete='cascade', related_sudo=True)
    domain_hash = fields.Char(string='Machine/Domain ID', help='Hash of the machine or domain for which the license file was downloaded.', size=16, required=True)
    client_hash = fields.Char(string='Application ID', help='Hash of the Bridge application for which the license file was downloaded.', size=16, required=True)
    user_hash = fields.Char(string='User ID', help='Hash of the user (group) that downloaded the license file.', size=32, compute='_compute_user_hash')
    num_downloads = fields.Integer(string='Downloads', help='Number of times the license file has been downloaded.', default=1)
    customer_name = fields.Char(string='Customer Name', related='license_id.customer_name', store=False, readonly=True)
    end_user = fields.Char(string='End User', related='license_id.end_user', store=False, readonly=True)
    status = fields.Selection(string='Status', related='license_id.status', store=False, readonly=True)
    notes = fields.Text(string='Notes', help='Additional notes related to the license file.')

    @api.depends('domain_hash', 'client_hash')
    def _compute_user_hash(self):
        for record in self:
            if not record.domain_hash or not record.client_hash:
                record.user_hash = False
                continue
            record.user_hash = f'{record.domain_hash}{record.client_hash}'
