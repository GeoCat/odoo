from typing import Any

from ..lib import utils

from odoo import api, fields, models, tools


LICENSE_STATUS = [
    ('issued', "Issued / Unused"),  # This status is never returned on checkout: it is the initial state
    ('active', "Active"),           # Default status when license is valid (and was checked out at least once)
    ('expired', "Expired"),         # License has expired (e.g. user did not renew in time)
    ('suspended', "Suspended"),     # Temporarily disabled by GeoCat (e.g. because of abuse)
    ('terminated', "Revoked")       # Contract was terminated
]


class License(models.Model):
    """ Class for GeoCat subscription-based software licenses.

    A new license record is created when the sale order matching a subscription sale order line with 1+ seats
    has been confirmed and invoiced/paid.
    Whenever the subscription sale order is updated, the license record(s) belonging to it are updated.
    Licenses are never automatically removed, only suspended or revoked.
    """

    _name = 'license.keys'
    _table = 'license_keys'
    _description = 'GeoCat Bridge Licenses'

    _sql_constraints = [
        ('key_unique', 'unique(key)', 'License key must be unique.')
    ]

    # Unique license key. This is generated once and cannot be changed.
    key = fields.Char(string='License Key', required=True, copy=False,
                      readonly=True, index=True, size=35, default=utils.generate_bridge_key,
                      help='Unique license key. This is generated once and cannot be changed.')

    # Keep reference to the sale.order.line that this license is associated with.
    # The sale.order.line also mentions the number of seats that are included in the license.
    # Note that if the order (line) is deleted, we do NOT necessarily want to delete the license!
    order_line_id = fields.Many2one('sale.order.line', string='Order Line Reference',
                                    required=True, ondelete='restrict', copy=False, index=True)
                                    # related=['num_bridge_seats', 'next_invoice_date', 'state', 'invoice_status'])

    # License status. This is used to determine if the license is still valid (along with the expiry/renewal date).
    status = fields.Selection(LICENSE_STATUS, string='Status', required=True, default='issued', index=True,
                              help='Current license status. Issued means that the license was created, '
                                   'but never checked out.')

    # Extended license expiry date. The license expiry date is normally based on the subscription renewal date.
    # However, there may be cases where we need to override this date (e.g. when there are payment issues).
    extended_date = fields.Date(string='Extended Expiry Date', copy=False,
                                help='Manually override (extend) the subscription renewal/expiry date.')

    # Number of seats that this license is valid for. This is taken from the ordered product by default.
    seats = fields.Integer(string='Seats', default=1, help='Number of seats (simultaneous users) for this license.')

    # End user name. This is optional and can also be set by the customer. Does not need to be a portal user.
    end_user = fields.Char(string='End User',
                           help='Optional end user or group name of this license key.\n'
                                'The specified name is displayed in the software as the licensed user.\n'
                                'If omitted, the customer name from the linked order will be used.')

    # Custom notes
    notes = fields.Text(string='Notes', help='Custom remarks or label related to this license key.')

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

    @api.constrains('order_line_id')
    def test(self):
        pass

    def license_response(self, token_hash: str) -> dict[str, Any]:
        """ Returns a dictionary with the license data to return to the user as JSON. """
        self.ensure_one()

        if self.order_line_id is None or self.order_line_id.num_bridge_seats < 1:
            raise ValueError("License is not associated with a valid order line.")

        # Determine expiry date
        expiry_date = self.order_line_id.next_invoice_date
        if not expiry_date:
            if self.extended_date:
                expiry_date = self.extended_date
            else:
                # Should not happen
                raise ValueError("License expiry date is not set.")
        if expiry_date < self.extended_date:
            expiry_date = self.extended_date

        # Determine (and update) license status
        status = self.status
        if status in ('issued', 'active'):
            if expiry_date < fields.Date.today():
                status = 'expired'
            elif status == 'issued':
                status = 'active'
            self.write({'status': status})

        # Return the license data
        response = {
            'status': status,
            'maxSeats': self.seats,
            'licensePlan': self.order_line_id.product_id.name,
            'validUntil': expiry_date,
            'companyName': self.order_line_id.order_id.partner_id.name,
            'hash': token_hash
        }
        if self.end_user:
            response['endUser'] = self.end_user

        return response
