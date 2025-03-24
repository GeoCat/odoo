# -*- coding: utf-8 -*-
import hashlib
import shutil
import zipfile
import werkzeug
import tempfile
from pathlib import Path

from ..lib import utils

from odoo import http, _
from odoo.http import request


class CveController(http.Controller):
    """ This controller allows us to push MkDocs documentation related to CVE's from GitHub to Odoo.
    It also provides a generic endpoint to view the docs (logged-in portal and internal users only).
    """
    cve_static_root = utils.module_base_path() / 'static' / 'cve'

    @http.route('/cve/publish', methods=['POST'], auth='bearer', csrf=False)
    def publish_cve(self, file, checksum):
        """ This route will allow us to push a .zip from GitHub to Odoo to 'publish' the CVE articles. """

        if not file or (file.content_type != 'application/zip' or file.mimetype != 'application/zip'):
            return request.make_json_response({'error': _('Missing zip file')}, status=400)
        if not checksum:
            return request.make_json_response({'error': _('Missing checksum')}, status=400)

        # Create temporary directory
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
            shutil.rmtree(tmp_dir)

    @http.route(['/cve', '/cve/<path:path>'], methods=['GET'], type='http', auth='user')
    def access_cve_articles(self, path=None, **kwargs):
        """ This route will make sure that CVE articles can be accessed by logged-in users only. """
        file_path = self.cve_static_root / path.strip('/') if path else self.cve_static_root
        if file_path.is_dir():
            file_path /= 'index.html'
        if not file_path.is_file():
            raise request.not_found()  # TODO: Show themed page?

        # Serve the file content as HTML
        return request.make_response(file_path.read_text(), headers=[('Content-Type', 'text/html')])
