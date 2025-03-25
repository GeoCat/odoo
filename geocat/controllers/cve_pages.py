# -*- coding: utf-8 -*-
import hashlib
import logging
import shutil
import zipfile
import werkzeug
import tempfile
from pathlib import Path
from mimetypes import guess_type

from ..lib import utils

from odoo import http, _
from odoo.http import request
from odoo.addons.web.controllers import binary

_logger = logging.getLogger(__name__)


class CveController(http.Controller):
    """ This controller allows us to push MkDocs documentation related to CVE's from GitHub to Odoo.
    It also provides a generic endpoint to view the docs (logged-in portal and internal users only).
    """
    cve_static_root = utils.module_base_path() / 'static' / 'cve'

    @http.route('/cve/publish', methods=['POST'], auth='bearer', csrf=False, cors='*.github.com')
    def publish_cve(self, file: werkzeug.datastructures.FileStorage, checksum: str):
        """ This route will allow us to push a .zip from GitHub to Odoo to 'publish' the CVE articles. """

        mime_type = file.content_type or file.mimetype or ''
        _logger.info(f"Initiating CVE publication from file '{file.name}' with MIME type '{mime_type}'")
        if not file or ('zip' not in mime_type or 'octet-stream' not in mime_type):
            return request.make_json_response({'error': _('Missing archive file')}, status=400)
        if not checksum:
            return request.make_json_response({'error': _('Missing checksum')}, status=400)

        # Set temporary directory path
        tmp_dir = Path(tempfile.mkdtemp())
        tmp_file_path = tmp_dir / werkzeug.utils.secure_filename(file.filename)

        try:
            # Save the file to the temporary directory
            with open(tmp_file_path, 'wb') as f:
                file.save(f)

            # Calculate checksum of the written file
            with open(tmp_file_path, 'rb') as f:
                received_checksum = hashlib.md5(f.read()).hexdigest()

            # Verify checksum
            if received_checksum != checksum:
                return request.make_json_response({'error': _('Bad checksum')}, status=400)

            # (Re)create the output folder
            if self.cve_static_root.exists():
                shutil.rmtree(self.cve_static_root, ignore_errors=True)
            self.cve_static_root.mkdir(parents=True, exist_ok=True)

            # Unpack the zip file to the final destination
            with zipfile.ZipFile(tmp_file_path, 'r') as zip_ref:
                zip_ref.extractall(self.cve_static_root)

            return request.make_json_response({'message': _('Published successfully')}, status=201)

        finally:
            # Clean up after ourselves
            shutil.rmtree(tmp_dir)

    @http.route(['/cve', '/cve/<path:path>'], methods=['GET'], type='http', auth='user')
    def access_cve(self, path=None, **kwargs):
        """ This route will make sure that CVE articles (and static files) can be accessed by logged-in users only. """
        base_dir = str(self.cve_static_root)
        file_path = Path(werkzeug.security.safe_join(str(base_dir), path.strip('/')) if path else base_dir)
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
            # File was not requested by the HTML and we're trying to access a static MkDocs asset: disallow direct access
            raise werkzeug.exceptions.Forbidden()
        return binary.send_file(file_path, request.httprequest.environ, mimetype=mime_type)
