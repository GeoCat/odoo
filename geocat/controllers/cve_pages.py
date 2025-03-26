# -*- coding: utf-8 -*-
import logging
import werkzeug
from pathlib import Path
from mimetypes import guess_type

from ..lib import utils

from odoo import http
from odoo.http import request
from odoo.addons.web.controllers import binary

_logger = logging.getLogger(__name__)


class CveController(http.Controller):
    """ This controller allows us to push MkDocs documentation related to CVE's from GitHub to Odoo.
    It also provides a generic endpoint to view the docs (logged-in portal and internal users only).
    """
    cve_static_root = str(utils.module_base_path() / 'static' / 'cve')

    @http.route(['/cve', '/cve/<path:path>'], methods=['GET'], type='http', auth='user')
    def access_cve(self, path=None, **kwargs):
        """ This route will make sure that CVE articles (and static files) can be accessed by logged-in users only. """
        file_path = Path(werkzeug.security.safe_join(self.cve_static_root, path.strip('/')) if path else self.cve_static_root)
        if file_path.is_dir():
            # If the user requests a directory, try to serve the index.html file inside it
            file_path /= 'index.html'
        if not file_path.is_file():
            raise request.not_found()

        # Guess the MIME type of the file
        mime_type, _ = guess_type(file_path)
        if not mime_type:
            mime_type = 'application/octet-stream'

        # Serve the file content
        if 'html' in mime_type:
            # Non-cached HTML response
            return request.make_response(
                file_path.read_text(),
                headers=[
                    ('Content-Type', mime_type),
                    ('Cache-Control', 'no-cache, no-store, must-revalidate'),
                ]
            )

        # Binary file (e.g. images, CSS, etc.)
        referer = request.httprequest.headers.get('Referer')
        if not referer and 'assets' in (p.name for p in file_path.parents):
            # File was not requested by the HTML and we're trying to access a static MkDocs asset:
            # disallow direct access like this
            raise werkzeug.exceptions.Forbidden()
        return binary.send_file(file_path, request.httprequest.environ, mimetype=mime_type)
