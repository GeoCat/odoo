from odoo.addons.website_helpdesk.controllers.main import WebsiteHelpdesk

from ..models.helpdesk_ticket import TICKET_CLASS, DEFAULT_CLASS


class GeoCatHelpdesk(WebsiteHelpdesk):

    def get_helpdesk_team_data(self, team, search=None):
        """ Override to add our custom ticket classifications so we can dynamically populate a selector. """
        return {
            'team': team,
            'main_object': team,
            'classifications': TICKET_CLASS,
            'default_classification': DEFAULT_CLASS,
        }
