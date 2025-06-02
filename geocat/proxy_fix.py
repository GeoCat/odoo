from werkzeug.middleware.proxy_fix import ProxyFix

from odoo import http as odoo_http


class ProxyFixApplication(ProxyFix):
    """ Custom version of Werkzeug's ProxyFix middleware that allows access to Odoo's application attributes.
    For example, 'session_store' can be accessed as 'odoo.http.root.session_store'.
    """
    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)

    def __getattr__(self, name):
        # Check if the attribute exists on the application and return it
        if hasattr(self.app, name):
            return getattr(self.app, name)
        # Raise AttributeError if the attribute is not found
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


# Wrap Odoo's Application instance in our custom ProxyFix
# so requests to our reverse proxy are logged with the client IPs in Odoo.
# See https://werkzeug.palletsprojects.com/en/3.0.x/middleware/proxy_fix/
# and https://www.odoo.com/my/tasks/4829751 (requires Odoo customer account)
# and geocat/geocat/__init__.py for the uninstall hook that removes this middleware.
# TODO: Uncertain if this works - we don't observe proper logging of client IPs in Odoo yet. For now we disable it, as it may be a security risk.
# odoo_http.root = ProxyFixApplication(odoo_http.root, x_for=1, x_proto=1, x_host=1)
