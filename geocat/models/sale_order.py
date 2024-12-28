from odoo import models, api, fields


class GeoCatSaleOrder(models.Model):
    """ Override that sets some default values for (new) sale orders like payment term and recurring plan. """

    _inherit = 'sale.order'

    license_count = fields.Integer(compute='_compute_license_count', search='_search_license_count', string='Bridge License Count')

    @api.depends('order_line.bridge_licenses')
    def _compute_license_count(self):
        for order in self:
            order.license_count = len(order.mapped('order_line.bridge_licenses'))

    @api.model
    def _search_license_count(self, operator, value):
        if operator not in ['=', '!=', '<', '>'] or not isinstance(value, int):
            raise NotImplementedError('Operation not supported.')
        sale_orders = self.env['sale.order'].search([])
        if operator == '=':
            sale_orders = sale_orders.filtered(lambda m: len(m.order_line.bridge_licenses) == value)
        elif operator == '!=':
            sale_orders = sale_orders.filtered(lambda m: len(m.order_line.bridge_licenses) != value)
        elif operator == '<':
            sale_orders = sale_orders.filtered(lambda m: len(m.order_line.bridge_licenses) < value)
        elif operator == '>':
            sale_orders = sale_orders.filtered(lambda m: len(m.order_line.bridge_licenses) > value)
        return [('id', 'in', sale_orders.ids)]

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
    #
    # @api.onchange('state', 'order_line', 'subscription_state', 'plan_id')
    # def _update_max_seats(self):
    #     for order in self:
    #         if not order.order_line:
    #             continue
    #         self.order_line._update_bridge_seats()
