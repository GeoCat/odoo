from odoo import http
from odoo.addons.website_helpdesk.controllers.main import WebsiteHelpdesk

from ..models.helpdesk_ticket import TICKET_CLASS, DEFAULT_CLASS


class GeoCatHelpdesk(WebsiteHelpdesk):

    # Make sure that our helpdesk route requires portal user authentication (i.e. not public)
    @http.route(['/helpdesk', '/helpdesk/<model("helpdesk.team"):team>'], type='http', auth='user', website=True, sitemap=True)
    def website_helpdesk_teams(self, team=None, **kwargs):
        return super().website_helpdesk_teams(team, **kwargs)

    def get_helpdesk_team_data(self, team, search=None):
        """ Override to add our custom ticket classifications so we can dynamically populate a selector. """
        return {
            'team': team,
            'main_object': team,
            'classifications': TICKET_CLASS,
            'default_classification': DEFAULT_CLASS,
        }
