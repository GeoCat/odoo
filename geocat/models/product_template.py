from odoo import fields, models, api


class LicensedProductTemplate(models.Model):
    """ Extends the product.template model to include the number of included GeoCat Bridge seats.

    When this is set to a value greater than 0, a license key will be generated for each sold product.
    """

    _inherit = 'product.template'

    can_have_bridge_licenses = fields.Boolean(
        string='Enabled',
        compute='_compute_can_have_bridge_licenses'
    )

    bridge_plan_name = fields.Char(
        string='Plan Name',
        help='The name of the GeoCat Bridge subscription plan for this product.\n'
             'This will be visible in the license details in the software.',
        compute='_compute_bridge_plan_name', readonly=False,
        store=True
    )

    bridge_seats = fields.Integer(
        string='Total Seats',
        help='A value of 0 means that this product does not include any GeoCat Bridge licenses.\n'
             'Values greater than 0 will allow you to generate 1 or more license keys for each '
             'sold subscription. You can freely distribute seats among the issued licenses until the set '
             'total here has been reached.',
        default=0
    )

    @api.depends('name')
    def _compute_bridge_plan_name(self):
        for product in self:
            if product.bridge_plan_name:
                continue
            product.bridge_plan_name = product.name

    @api.depends('bridge_seats')
    def _compute_can_have_bridge_licenses(self):
        for product in self:
            product.can_have_bridge_licenses = product.bridge_seats > 0
