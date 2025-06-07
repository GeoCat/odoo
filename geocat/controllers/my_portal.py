from odoo.http import route, request
from odoo.addons.portal.controllers.portal import CustomerPortal as BaseCustomerPortal


class CustomerPortal(BaseCustomerPortal):
    """ Override the CustomerPortal to ensure that our custom portal layout is used. """

    @route(['/my', '/my/home', '/support'], type='http', auth="user", website=True)
    def home(self, **kw):
        values = self._prepare_portal_layout_values()
        values.update(self._prepare_home_portal_values([]))
        return request.render("geocat.portal_my_home_no_cards", values)
