from odoo import models, api, fields


class GeoCatSaleOrderLine(models.Model):
    """ . """

    _inherit = 'sale.order.line'

    # === FIELD DEFINITIONS ===
    bridge_licenses = fields.One2many('geocat.license.keys', 'order_line_id', string='Bridge Keys',
                                      help='Bridge license keys attached to the ordered subscription plan.',
                                      readonly=True)

    max_bridge_seats = fields.Integer(string='Max. Bridge Seats', compute='_compute_max_seats', store=True,
                                      help='The maximum number of included Bridge seats for the ordered plan and quantity.')

    display_name = fields.Char(compute='_compute_display_name', readonly=True)

    # hide_bridge_license_issue_button = fields.Boolean(compute='_compute_hide_license_buttons',
    #                                                   help='Whether the "Issue License" button should be hidden.')
    #
    # hide_bridge_license_show_button = fields.Boolean(compute='_compute_hide_license_buttons',
    #                                                  help='Whether the "Show Licenses" button should be hidden.')

    @api.depends()
    def _compute_display_name(self):
        i = 1
        for line in self:
            names = line.name.splitlines()
            name = names[0]
            description = ''
            if len(names) > 1:
                description = f' ({", ".join(names[1:])})'
            line.display_name = f'{name}{description} - {line.order_id.name} - {line.order_id.partner_id.name}'
            i += 1

    @api.depends('product_template_id', 'product_id', 'qty_invoiced', 'product_uom_qty', 'order_id')
    def _compute_max_seats(self):
        for order in self:
            is_subscription = order.order_id.is_subscription
            quantity = int(order.qty_invoiced or order.product_uom_qty)
            if not order.product_template_id or quantity == 0 or not is_subscription:
                order.max_bridge_seats = 0
                continue
            order.max_bridge_seats = order.product_template_id.bridge_seats * quantity

    # def issue_new_license(self):
    #     self.ensure_one()
    #     return {
    #         "type": "ir.actions.act_window",
    #         "res_model": "geocat.license.keys",
    #         "views": [[False, "form"]],
    #         "context": {
    #             'order_id': self.order_id,
    #             'default_order_line_id': self.id,
    #         },
    #     }
    #
    # def view_licenses(self):
    #     self.ensure_one()
    #     return {
    #         "type": "ir.actions.act_window",
    #         "res_model": "geocat.license.keys",
    #         "views": [[False, "list"]],
    #         "context": {
    #             'order_id': self.order_id,
    #             'default_order_line_id': self.id,
    #         },
    #     }

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
