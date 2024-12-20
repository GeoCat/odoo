from odoo import models, api, fields


class GeoCatSaleOrderLine(models.Model):
    """ . """

    _inherit = 'sale.order.line'

    @api.depends('product_template_id', 'product_id', 'qty_invoiced', 'product_uom_qty')
    def _compute_max_seats(self):
        for order in self:
            quantity = int(order.qty_invoiced or order.product_uom_qty)
            if (not order.product_template_id or quantity == 0
                    or order.order_id.state != 'sale'
                    or not order.order_id.is_subscription):
                order.max_bridge_seats = 0
                continue
            order.max_bridge_seats = order.product_template_id.bridge_seats * quantity

    # === FIELD DEFINITIONS ===
    bridge_licenses = fields.One2many('geocat.license.keys', 'order_line_id', string='Bridge Keys',
                                      help='Included Bridge license keys for the ordered subscription plan.',
                                      readonly=True)

    max_bridge_seats = fields.Integer(string='Max. Bridge Seats', compute=_compute_max_seats, store=True,
                                      help='The maximum number of included Bridge seats for the ordered plan and quantity.')

    # @api.depends('product_template_id')
    # def _compute_max_bridge_seats(self):
    #     for order in self:
    #         order.max_bridge_seats = sum(order.order_line.mapped('product_template_id.num_bridge_seats'))
    #
    # @api.depends('partner_id')
    # def _compute_payment_term_id(self):
    #     default_term = self.env['account.payment.term'].search([('is_default', '=', True), ('active', '=', True)], limit=1)
    #     for order in self:
    #         order = order.with_company(order.company_id)
    #         partner_term_id = order.partner_id.property_payment_term_id
    #         if partner_term_id:
    #             order.payment_term_id = partner_term_id
    #         elif not order.payment_term_id and default_term:
    #             order.payment_term_id = default_term[0].id
    #
    # @api.depends('sale_order_template_id')
    # def _compute_plan_id(self):
    #     default_plan = self.env['sale.subscription.plan'].search([('is_default', '=', True), ('active', '=', True)], limit=1)
    #     for order in self:
    #         if order.sale_order_template_id and order.sale_order_template_id.plan_id:
    #             order.plan_id = order.sale_order_template_id.plan_id
    #         elif default_plan:
    #             order.plan_id = default_plan[0].id
