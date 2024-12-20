from odoo import http
from odoo.http import request
import werkzeug


class LicenseCheckout(http.Controller):
    @http.route(['/licensing/checkout'], auth='public', methods=['GET', 'PUT', 'DELETE', 'PATCH'], type='http')
    def process_request(self):
        """
        Redirect non-POST requests to the portal.
        """
        return werkzeug.utils.redirect('/')

    @http.route(['/licensing/checkout'], auth='public', methods=['POST'], csrf=False)
    def checkout_license(self):
        """
        Returns a license response whenever a POST with a JSON body is done on the endpoint.
        """
        media_type = request.httprequest.headers.get('Accept', '*/*')
        if not (media_type.startswith('application') and media_type.endswith('json')):
            # Redirect to home page if something other than JSON is requested.
            return werkzeug.utils.redirect('/')
        # TODO: process JSON body, fetch license data, return JSON response
        return request.make_json_response({"message": "it worked"})


