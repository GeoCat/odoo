from odoo import http
from odoo.http import request, route


class LicenseCheckout(http.Controller):
    @http.route(['/checkout'], type='json', auth='public')  # TODO: methods=['POST']
    def checkout_license(self):
        """
        Returns a license response.
        """
        return request.make_json_response({"message": "it worked"})
