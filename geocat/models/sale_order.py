from odoo import models, api, fields


class GeoCatSaleOrder(models.Model):
    """ Override that sets some default values for (new) sale orders like payment term and recurring plan. """

    _inherit = 'sale.order'

    @api.depends('partner_id')
    def _compute_payment_term_id(self):
        default_term = self.env['account.payment.term'].search([('is_default', '=', True), ('active', '=', True)], limit=1)
        for order in self:
            order = order.with_company(order.company_id)
            partner_term_id = order.partner_id.property_payment_term_id
            if partner_term_id:
                order.payment_term_id = partner_term_id
            elif not order.payment_term_id and default_term:
                order.payment_term_id = default_term[0].id

    @api.depends('sale_order_template_id')
    def _compute_plan_id(self):
        default_plan = self.env['sale.subscription.plan'].search([('is_default', '=', True), ('active', '=', True)], limit=1)
        for order in self:
            if order.sale_order_template_id and order.sale_order_template_id.plan_id:
                order.plan_id = order.sale_order_template_id.plan_id
            elif default_plan:
                order.plan_id = default_plan[0].id
