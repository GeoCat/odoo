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
        safe_path = werkzeug.security.safe_join(self.cve_static_root, path.strip('/')) if path else None
        file_path = Path(safe_path if safe_path else self.cve_static_root)
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
            # Read HTML content into memory
            html_content = file_path.read_text()

            # Inject <base> tag to make sure relative links work properly
            requested_path = Path(request.httprequest.path)
            if requested_path.suffix.startswith('.htm'):
                # If an actual HTML file path was requested, use its directory path
                requested_path = requested_path.parent
            base_tag = f'<base href="{requested_path}/" />'
            html_content = html_content.replace('<head>', f'<head>\n{base_tag}\n')

            # Return HTML as non-cachable response
            return request.make_response(
                html_content,
                headers=[
                    ('Content-Type', mime_type),
                    ('Cache-Control', 'no-cache, no-store, must-revalidate'),
                ]
            )

        # We are dealing with a binary file (e.g. images, CSS, etc.)
        referer = request.httprequest.headers.get('Referer')
        if not referer and 'assets' in (p.name for p in file_path.parents):
            # File was not requested by the HTML and we're trying to access a static MkDocs asset:
            # disallow direct access like this
            raise werkzeug.exceptions.Forbidden()

        # Serve the file using the binary controller
        return binary.send_file(file_path, request.httprequest.environ, mimetype=mime_type)
