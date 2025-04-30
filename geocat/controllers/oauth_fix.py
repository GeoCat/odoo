# -*- coding: utf-8 -*-
import json
import logging
import urllib.parse

import werkzeug.urls
import werkzeug.utils

from odoo.http import request
from odoo.addons.auth_oauth.controllers.main import OAuthLogin


_logger = logging.getLogger(__name__)


# noinspection DuplicatedCode,PyUnresolvedReferences
class GeoCatOAuthLogin(OAuthLogin):
    """ Customized OAuth login controller to enforce the base URL from the Odoo configuration instead of the requested URL root.
    The reason for this is that the Google authentication (also for API requests) sometimes seems to fail due to URL mismatches.
    See https://github.com/odoo/odoo/issues/138727.
    """

    @staticmethod
    def _get_base_url():
        """ Get the base URL from the Odoo configuration (or use fallback). """
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if not base_url or not base_url.startswith('https://'):
            _logger.error("Invalid or non-secure base URL: %s", base_url)
            base_url = request.httprequest.url_root  # Fallback to actual requested URL
        return base_url

    def list_providers(self):
        """ Basically the same as the Odoo 18 original, except for the base URL fix. """
        try:
            providers = request.env['auth.oauth.provider'].sudo().search_read([('enabled', '=', True)])
        except Exception:
            providers = []

        for provider in providers:
            return_url = urllib.parse.urljoin(self._get_base_url(), 'auth_oauth/signin')
            state = self.get_state(provider)
            params = dict(
                response_type='token',
                client_id=provider['client_id'],
                redirect_uri=return_url,
                scope=provider['scope'],
                state=json.dumps(state),
            )
            provider['auth_link'] = "%s?%s" % (provider['auth_endpoint'], werkzeug.urls.url_encode(params))
        return providers

    def get_state(self, provider):
        """ Basically the same as the Odoo 18 original, except for the base URL fix. """
        redirect = request.params.get('redirect') or 'web'
        if not redirect.startswith(('//', 'http://', 'https://')):
            redirect = '%s%s' % (self._get_base_url(), redirect[1:] if redirect[0] == '/' else redirect)
        state = dict(
            d=request.session.db,
            p=provider['id'],
            r=werkzeug.urls.url_quote_plus(redirect),
        )
        token = request.params.get('token')
        if token:
            state['t'] = token
        return state
