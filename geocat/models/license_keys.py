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

    _sql_constraints = [
        ('key_unique', 'unique(key)', 'License key must be unique.'),
        ('key_not_null', 'CHECK(key IS NOT NULL)', 'License key cannot be NULL.')
    ]

    def _generate_key(self):
        """ Generates a new unique 35-char license key. """
        new_key = utils.generate_bridge_key()
        while self.search_count([('key', '=', new_key)]) > 0:
            new_key = utils.generate_bridge_key()
        return new_key

    # def _is_sold_subscription(self) -> bool:
    #     """ Check if the order was placed and is a subscription. """
    #     return self.order_id and self.order_id.state == 'sale' and self.order_id.is_subscription

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
            record.display_name = '-'.join([record.key[i:i+5] for i in range(0, len(record.key), 5)])

    # @api.constrains('seats')
    # def _compute_seats(self):
    #     lookup = {}
    #     for row in self.env['license.keys'].search([('order_id', '!=', None), ('order_id.max_bridge_seats', '>', 0)]):
    #         lookup.setdefault(row.order_id.id, 0)
    #         lookup[row.order_id.id] += row.seats
    #
    #     # Now check if
    #     for record in self:
    #         max_seats = record.order_id.max_bridge_seats if record.order_id else 0
    #         if max_seats == 0:
    #             raise ValidationError("License must be associated with an order that includes Bridge seats.")
    #
    #
    #         if not record._is_sold_subscription():
    #             record.seats = 1
    #         else:
    #             record.seats = record.order_id.max_bridge_seats

    # === FIELD DEFINITIONS ===

    # Unique license key. This is generated once and cannot be changed.
    key = fields.Char(string='Internal Key', index=True, size=35, default=_generate_key, readonly=True,
                      help='Unique license key. This is generated once and cannot be changed.')

    # For human-readable display purposes, we show the key in groups of 5 characters.
    display_name = fields.Char(string='License Key', compute='_compute_display_name', readonly=True)

    # Keep reference to the sale.order that this license is associated with.
    # The maximum number of seats that a license can support are computed based on the ordered product templates (num_bridge_seats).
    # Note that if the order is deleted, we do NOT necessarily want to delete the license!
    order_line_id = fields.Many2one('sale.order.line', string='Subscription Plan', index=True, required=True, copy=True,
                                    domain="[('order_id.is_subscription', '=', True), ('state', '=', 'sale'), ('max_bridge_seats', '>', 0)]",
                                    ondelete='cascade', help='Reference to the sold subscription plan this license key is associated with.')

    # License status. This is used to determine if the license is still valid (along with the expiry/renewal date).
    status = fields.Selection(LICENSE_STATUS, string='Status', required=True, default='issued', index=True,
                              help='Current license status. Issued means that the license was created, '
                                   'but never checked out (or downloaded) by the customer.')

    # Extended license expiry date. The license expiry date is normally based on the subscription renewal date.
    # However, there may be cases where we need to override this date (e.g. when there are payment issues).
    expiry_date = fields.Date(string='Expiry Date', compute=_compute_expiry_date, store=True,
                              help='Manually override (extend) the subscription renewal/expiry date.\n'
                                   'If omitted, the next invoice date from the linked order will be used.')

    # Number of seats that this license is valid for. This is taken from the ordered product by default.
    seats = fields.Integer(string='Seats', default=1, help='Number of seats (simultaneous users) for this license key.')

    # End user name. This is optional and can also be set by the customer. Does not need to be a portal user.
    end_user = fields.Char(string='End User', default=None, copy=False,
                           help='Optional name of the end user(s) of this license key.\n'
                                'The specified name is displayed in the software as the licensed user(s).\n'
                                'If omitted, the customer name from the linked order will be used.')

    # Whether the customer is allowed to download a license file for this key. Default is True.
    allow_download = fields.Boolean(string='Allow Download', default=True,
                                    help='Allow the customer to download offline license files (.lic).')

    # Custom notes
    notes = fields.Text(string='Internal Notes', help='Custom remarks or label related to this license key.')

    # Related licenses (on same subscription sale order)
    related_licenses = fields.One2many('geocat.license.keys', string='Related Keys', store=False,
                                       related='order_line_id.bridge_licenses', readonly=True,
                                       help='Other license keys on the same subscription.',
                                       domain="[('key', '!=', self.key)]")

    # checkouts: fields.One2many
    # downloads: OneToMany
    # expires: date(default: now + 1
    # yr)
    # status: str[LicenseStatus]
    # end_user: nullable
    # str
    # notes(?)

    # @api.onchange('order_line_id')
    # def _update_license(self):
    #     """ Compute the expiry date based on the order and update the license status accordingly. """
    #     for line in self:
    #         order_line = line.order_line_id
    #
    #         if not order_line or not order_line.num_bridge_seats > 0 or order_line.state == 'cancel':
    #             # Suspend if the order is lost or cancelled, or the number of seats is not set (or 0):
    #             # This means that an action is required by GeoCat or the customer.
    #             line.status = 'suspended'
    #             line.extended_date = None
    #             continue
    #
    #         if order_line.next_invoice_date
    #
    #         if order_line.order_id.subscription_state in ('3_progress', :
    #
    #         line.expires = order_line.order_id.

    # @api.constrains('order_line_id')
    # def test(self):
    #     pass

    # def unlink(self):
    #     raise UserError(_("License keys cannot be deleted!"))

    # def toggle_active(self):
    #     """ Toggles the license status between active and suspended. """
    #     self.ensure_one()
    #     if self.status == 'active':
    #         self.status = 'suspended'
    #     elif self.status in ('suspended', 'terminated'):
    #         self.status = 'active'

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
