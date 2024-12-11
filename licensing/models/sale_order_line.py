from odoo import fields, models, api


class LicensedSaleOrderLine(models.Model):
    """ Extends the sale.order.line model to include the number of included GeoCat Bridge seats.

    This number is taken from the product template, but it can also be explicitly set/overridden.
    """
    _inherit = 'sale.order.line'

    num_bridge_seats = fields.Integer(
        string='Bridge Seats',
        help="""Values greater than 0 will cause one Bridge license key to be generated for each sold product.
A license key will be valid for the number of seats (simultaneous users) specified here.""",
        compute='_compute_seats',
        readonly=False,
        store=True
    )

    licenses = fields.One2many('license.keys', 'order_line_id', string='License Keys', copy=False,
                               help='Generated Bridge license keys that belong to this order line.', readonly=True)

    @api.onchange('product_id', 'product_template_id')
    @api.depends('product_id', 'product_template_id')
    def _compute_seats(self):
        for line in self:
            if not line.product_id or line.num_bridge_seats > 0:
                # Do not compute if there is no product, or the number of seats is already set
                continue

            line.num_bridge_seats = line._get_seats_from_template()

    def _get_seats_from_template(self):
        self.ensure_one()
        num_seats = self.num_bridge_seats
        if self.product_template_id and self.product_template_id.num_bridge_seats > 0:
            num_seats = self.product_template_id.num_bridge_seats
        return num_seats

    @api.onchange('num_bridge_seats', 'invoice_status', 'state', 'next_invoice_date')
    def _update_licenses(self):
        pass
