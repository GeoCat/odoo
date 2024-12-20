from odoo import models, api, fields


class DefaultSaleSubscriptionPlan(models.Model):
    """ Extends the sale.subscription.plan model to include an "is default" flag.

    There can only be 1 default term line at a time, or none at all.
    The default is used as the standard payment term for new sale orders.
    """

    _inherit = 'sale.subscription.plan'

    _sql_constraints = [
        ('value_check',
         "CHECK(is_default IS NOT NULL)",
         "is_default must be either true or false but not NULL."
         )
    ]

    is_default = fields.Boolean(string='Default', readonly=False, default=False,
                                help='Only one plan can be set as the default subscription plan.')

    def _unset_defaults(self):
        """ Unsets the default flag for all subscription plans. """
        self.env['sale.subscription.plan'].search([('is_default', '=', True)]).write({'is_default': False})

    @api.model_create_multi
    def create(self, vals):
        for v in vals:
            if v.get('is_default', False):
                self._unset_defaults()
        return super(DefaultSaleSubscriptionPlan, self).create(vals)

    def write(self, vals):
        if vals.get('is_default', False):
            self._unset_defaults()
        return super(DefaultSaleSubscriptionPlan, self).write(vals)
