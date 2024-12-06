from odoo import fields, models


class ProductTemplate(models.Model):
    """ Extends the product.template model to include the number of included GeoCat Bridge seats.

    When this is set to a value greater than 0, a license key will be generated for each sold product.
    """

    _inherit = 'product.template'

    num_bridge_seats = fields.Integer(
        string='Bridge Seats',
        help="""Values greater than 0 will cause one Bridge license key to be generated for each sold product.
A license key will be valid for the number of seats (simultaneous users) specified here.""",
        default=0
    )
