import werkzeug

from odoo import http


class GeoCatRouter(http.Controller):
    @http.route(['/docs/<path:path>'], type='http', auth='public')
    def redirect_docs(self, path):
        """ Redirect the /docs/<path> URL to the GeoCat documentation on docs.geocat.net (eos). """
        return werkzeug.utils.redirect(f'https://docs.geocat.net/{path}', 301)

    @http.route(['/news'], type='http', auth='public')
    def redirect_news(self):
        """ Redirect /news to the main blog page. The 'News' blog with ID 1 must exist! """
        return werkzeug.utils.redirect('/blog/news-1', 301)

    @http.route(['/news/<path:path>'], type='http', auth='public')
    def redirect_news_path(self, path):
        """ Redirect /news/<path> to the post in the 'News' blog with ID 1. """
        return werkzeug.utils.redirect(f'/blog/news-1/{path}', 301)
