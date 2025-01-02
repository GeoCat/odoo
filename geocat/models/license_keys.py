from typing import Any

from odoo.exceptions import ValidationError
from ..lib import utils

from odoo import api, fields, models

LICENSE_STATUS = [
    ('issued', "Issued / Unused"),  # This status is never returned on checkout: it is the initial state
    ('active', "Active"),           # Default status when license is valid (and was checked out at least once)
    ('expired', "Expired"),         # License has expired (e.g. user did not renew in time)
    ('suspended', "Suspended"),     # Temporarily disabled by GeoCat (e.g. because of abuse)
    ('terminated', "Revoked")       # Contract was terminated
]


class GeoCatBridgeLicense(models.Model):
    """ Class for GeoCat subscription-based software licenses.

    A new license record is created when the sale order matching a subscription sale order line with 1+ seats
    has been confirmed and invoiced/paid.
    Whenever the subscription sale order is updated, the license record(s) belonging to it are updated.
    Licenses are never automatically removed, only suspended or revoked.
    """

    _name = 'geocat.license.keys'
    _table = 'geocat_license_keys'
    _description = 'GeoCat Bridge Licenses'
    _order = 'order_line_id asc, create_date desc'
    _inherit = ["mail.thread"]

    _sql_constraints = [
        ('key_unique', 'unique(key)', 'License key must be unique.'),
        ('key_not_null', 'CHECK(key IS NOT NULL)', 'License key cannot be NULL.')
    ]

    # === FIELD DEFINITIONS ===

    # Unique license key. This is generated once and cannot be changed.
    key = fields.Char(string='Internal Key', index=True, size=35, readonly=True, compute='_generate_key', store=True,
                      help='Unique license key. Generated once and cannot be changed.', precompute=True)

    # For human-readable display purposes, we show the key in groups of 5 characters.
    display_name = fields.Char(string='License Key', compute='_compute_display_name', readonly=True,
                               search='_search_display_name')

    # Keep reference to the sale.order that this license is associated with.
    # The maximum number of seats that a license can support are computed based on the ordered product templates (num_bridge_seats).
    # Note that if the order is deleted, we do NOT necessarily want to delete the license!
    order_line_id = fields.Many2one('sale.order.line', string='Subscription Plan', index=True, required=True, copy=True,
                                    domain="[('order_id.is_subscription', '=', True), ('max_bridge_seats', '>', 0), "
                                           "('order_id.subscription_state', 'in', ('3_progress', '5_renewed'))]",
                                    ondelete='cascade', help='Reference to the associated subscription plan of the license key.',
                                    tracking=True)

    # License status. This is used to determine if the license is still valid (along with the expiry/renewal date).
    status = fields.Selection(LICENSE_STATUS, string='Status', required=True, default='issued', index=True,
                              help='Current license status. Issued means that the license was created, '
                                   'but never checked out (or downloaded) by the customer.', tracking=True)

    # Extended license expiry date. The license expiry date is normally based on the subscription renewal date.
    # However, there may be cases where we need to override this date (e.g. when there are payment issues).
    expiry_date = fields.Date(string='Expiry Date', compute='_compute_expiry_date', store=True, tracking=True,
                              help='Manually override (extend) the subscription renewal/expiry date.\n'
                                   'If omitted, the next invoice date from the linked order will be used.',
                              recursive=True)

    # Number of seats that this license is valid for. This is taken from the ordered product by default.
    seats = fields.Integer(string='Seats', default=1, tracking=True,
                           help='Number of seats (simultaneous users) for the license key.')

    # End user name. This is optional and can also be set by the customer. Does not need to be a portal user.
    end_user = fields.Char(string='End User', default=None, copy=False, tracking=True,
                           help='Optional name of the end user(s) of the license key.\n'
                                'The specified name is displayed in the software as the licensed user(s).\n'
                                'If omitted, the customer name from the linked order will be used.')

    # Whether the customer is allowed to download a license file for this key. Default is True.
    allow_download = fields.Boolean(string='Allow Download', default=True, tracking=True,
                                    help='Allow the customer to download offline license files (.lic).')

    # Custom notes
    notes = fields.Text(string='Internal Notes', help='Custom remarks or label related to this license key.')

    # Related licenses (on same subscription sale order)
    related_licenses = fields.One2many('geocat.license.keys', string='Related Keys', compute='_compute_related_licenses',
                                       help='Other license keys on the same subscription.', readonly=True, recursive=True)

    # Related checkouts and license file downloads
    checkouts = fields.One2many('geocat.license.checkouts', 'license_id', string='Key Checkouts', copy=False, readonly=True)
    downloads = fields.One2many('geocat.license.downloads', 'license_id', string='File Downloads', copy=False, readonly=True)
    num_checkouts = fields.Integer(string='Checkouts', compute='_compute_num_checkouts', readonly=True)
    num_downloads = fields.Integer(string='Downloads', compute='_compute_num_downloads', readonly=True)

    order_ref = fields.Char(string='Order Number', related='order_line_id.order_id.name', store=False, readonly=True)
    customer_name = fields.Char(string='Customer Name', related='order_line_id.order_partner_id.name', store=False, readonly=True)

    def _ensure_unique_key(self) -> str:
        new_key = utils.generate_bridge_key()
        while self.search_count([('key', '=', new_key)]) > 0:
            # Likely overkill, but in case of a collision, try again
            new_key = utils.generate_bridge_key()
        return new_key

    @api.depends('order_line_id')
    def _generate_key(self):
        """ Generates a new unique 35-char license key when a new record is created (and no key is present). """
        for lic in self:
            if utils.REGEX_LICKEY.match(lic.key or '') and self.search_count([('key', '=', lic.key)]) == 1:
                # Key has been set and exists only once: keep it
                continue
            # Generate a new unique key
            lic.key = self._ensure_unique_key()

    @api.depends('checkouts')
    def _compute_num_checkouts(self):
        for record in self:
            record.num_checkouts = sum(record.checkouts.mapped('num_checkouts'))

    @api.depends('downloads')
    def _compute_num_downloads(self):
        for record in self:
            record.num_downloads = sum(record.downloads.mapped('num_downloads'))

    @api.constrains('seats')
    def _check_seats(self):
        for lic in self:
            if not lic.order_line_id:
                continue
            max_seats = lic.order_line_id.max_bridge_seats
            if lic.seats > max_seats:
                raise ValidationError(f"Number of seats may not exceed the maximum ({max_seats}) for the current plan.")

    @api.depends('order_line_id')
    def _compute_expiry_date(self):
        for record in self:
            if not record.order_line_id or record.order_line_id.next_invoice_date == fields.Date.today():
                # If there is no order yet, or the invoice is from today, set the expiry date to a year from now
                record.expiry_date = utils.default_expiry_date()
            else:
                record.expiry_date = record.order_line_id.next_invoice_date

    @api.depends('expiry_date')
    def _update_status(self):
        for record in self:
            if not record.expiry_date:
                continue
            if record.expiry_date < fields.Date.today() and record.status in ('active', 'issued'):
                record.status = 'expired'
            elif record.status == 'expired' and record.expiry_date >= fields.Date.today():
                record.status = 'active'

    @api.depends('key')
    def _compute_display_name(self):
        for record in self:
            if not record.key:
                record.key = self._ensure_unique_key()
            record.display_name = '-'.join([record.key[i:i+5] for i in range(0, len(record.key), 5)])

    @api.depends('order_line_id')
    def _compute_related_licenses(self):
        self.ensure_one()
        order_id = self.order_line_id.order_id.id
        other_lics = self.env['geocat.license.keys'].search([('order_line_id.order_id.id', '=', order_id), ('id', '!=', self.id)])
        self.related_licenses = other_lics

    @api.model
    def _search_display_name(self, operator, value):
        value = str(value)
        if operator not in ['=', '!=', 'like', 'ilike']:
            raise NotImplementedError('Operation not supported.')
        licenses = self.env['geocat.license.keys'].search([])
        if operator == '=':
            licenses = licenses.filtered(lambda lic: lic.display_name == value)
        elif operator == '!=':
            licenses = licenses.filtered(lambda lic: lic.display_name != value)
        elif operator == 'like':
            licenses = licenses.filtered(lambda lic: value in lic.display_name)
        elif operator == 'ilike':
            licenses = licenses.filtered(lambda lic: value.casefold() in lic.display_name.casefold())
        return [('id', 'in', licenses.ids)]

    # checkouts: fields.One2many
    # downloads: OneToMany
    # expires: date(default: now + 1
    # yr)
    # status: str[LicenseStatus]
    # end_user: nullable
    # str
    # notes(?)

    def copy(self, default=None):
        """ Do not allow duplication of licenses. """
        raise ValidationError("License keys cannot be duplicated.")

    # @api.onchange('expiry_date')
    # def _update_status(self):
    #     """ Updates the status if the extended_date has been changed. """
    #     for record in self:
    #         if not record.expiry_date:
    #             # No change in status
    #             continue
    #         if record.expiry_date < fields.Date.today():
    #             record.status = 'expired'
    #         elif record.status == 'expired':
    #             record.status = 'active'
    #     if not self.expiry_date:
    #
    #         return
    #
    #     if not self.expiry_date or self.expiry_date < fields.Date.today():
    #         self.extended_date = fields.Date.today()

    def license_response(self, token_hash: str) -> dict[str, Any]:
        """ Returns a dictionary with the license data to return to the user as JSON. """
        self.ensure_one()

        # Check if the license is associated with a valid order
        if self.order_line_id is None or self.order_line_id.state != 'sale':
            raise ValueError("License is not associated with a valid GeoCat Bridge order.")
        total_seats = self.order_line_id.max_bridge_seats

        # Determine expiry date
        exp_date = self.order_line_id.next_invoice_date
        if not exp_date:
            if self.expiry_date:
                exp_date = self.expiry_date
            else:
                # Should not happen
                raise ValueError("License expiry date is not set.")
        if exp_date < self.expiry_date:
            exp_date = self.expiry_date

        # Determine (and update) license status
        self._update_status()
        if self.status == 'issued':
            self.update({'status': 'active'})

        plan_name = "GeoCat Bridge"
        if total_seats > 1:
            plan_name += " Enterprise Bundle"

        # Return the license data
        response = {
            'status': self.status,
            'maxSeats': self.seats,
            'licensePlan': plan_name,
            'validUntil': exp_date,
            'companyName': self.order_line_id.order_partner_id.name,
            'hash': token_hash
        }
        if self.end_user:
            response['endUser'] = self.end_user

        return response
