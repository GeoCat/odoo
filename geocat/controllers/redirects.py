import werkzeug
import logging
import urllib.parse

from odoo import http

_logger = logging.getLogger(__name__)


class GeoCatRouter(http.Controller):

    @staticmethod
    def _permanent_redirect(base_url: str, path: str = '', **kwargs):
        """ Redirect the request to a new URL (301). """
        url = f'{base_url.rstrip('/')}/{path.lstrip('/')}'
        if kwargs:
            url = f'{url.rstrip('/')}?{urllib.parse.urlencode(kwargs)}'
        return werkzeug.utils.redirect(url, 301)

    @http.route(['/docs'], type='http', auth='public')
    def redirect_docs(self, **kwargs):
        """ Redirect the /docs to docs.geocat.net (eos). """
        return self._permanent_redirect('https://docs.geocat.net', **kwargs)

    @http.route(['/docs/<path:path>'], type='http', auth='public')
    def redirect_docs_path(self, path, **kwargs):
        """ Redirect the /docs/<path> URL to the GeoCat documentation on docs.geocat.net (eos). """
        return self._permanent_redirect('https://docs.geocat.net', path, **kwargs)

    @http.route(['/news'], type='http', auth='public')
    def redirect_news(self, **kwargs):
        """ Redirect /news to the main blog page. The 'News' blog with ID 1 must exist! """
        return self._permanent_redirect('/blog/news-1', **kwargs)

    @http.route(['/news/<path:path>'], type='http', auth='public')
    def redirect_news_path(self, path, **kwargs):
        """ Redirect /news/<path> to the post in the 'News' blog with ID 1. """
        return self._permanent_redirect('/blog/news-1', path, **kwargs)

    @http.route(['/feed', '/feed/'], type='http', auth='public')
    def redirect_feed(self, **kwargs):
        """ Redirect /feed to the main blog feed. The 'News' blog with ID 1 must exist! """
        return self._permanent_redirect('/blog/news-1/feed', **kwargs)

    @http.route(['/wp-content/uploads/<path:path>'], type='http', auth='public')
    def redirect_wp_content(self, path, **kwargs):
        """ Redirect /wp-content/uploads/<path> to the archived media location. """
        return self._permanent_redirect('https://cdn.geocat.net/archive', path, **kwargs)
