from odoo import fields, models, api


class AccountPaymentTerm(models.Model):
    """ Extends the account.payment.term model to include an "is default" flag.

    There can only be 1 default term line at a time, or none at all.
    The default is used as the standard payment term for new sale orders.
    """

    _inherit = 'account.payment.term'

    _sql_constraints = [
        ('value_check',
         "CHECK(is_default IS NOT NULL)",
         "is_default must be either true or false but not NULL."
         )
    ]

    is_default = fields.Boolean(string='Default', readonly=False, default=False,
                                help='Only one term can be set as the default payment term.')

    def _unset_defaults(self):
        """ Unsets the default flag for all payment terms. """
        self.env['account.payment.term'].search([('is_default', '=', True)]).write({'is_default': False})

    @api.model_create_multi
    def create(self, vals):
        for v in vals:
            if v.get('is_default', False):
                self._unset_defaults()
        return super(AccountPaymentTerm, self).create(vals)

    def write(self, vals):
        if vals.get('is_default', False):
            self._unset_defaults()
        return super(AccountPaymentTerm, self).write(vals)
