from re import compile
from operator import itemgetter

from markupsafe import Markup
from werkzeug.exceptions import NotFound

from odoo import http, _, SUPERUSER_ID
from odoo.addons.helpdesk.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.addons.website_helpdesk.controllers.main import WebsiteHelpdesk, WebsiteForm
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.tools import groupby as groupbyelem
from ..models.helpdesk_ticket import TICKET_CLASS, DEFAULT_CLASS

HTML_TAG_PATTERN = compile(r'<[^>]+>')


class GeoCatCustomerPortal(CustomerPortal):

    def _ticket_get_searchbar_inputs(self):
        """ Remove the 'team_id' and 'stage_id' search fields, add 'consolidated_status' and 'classification'. """
        return {
            'name': {'input': 'name', 'label': _(
                'Search%(left)s Tickets%(right)s',
                left=Markup('<span class="nolabel">'),
                right=Markup('</span>'),
            ), 'sequence': 10},
            'user_id': {'input': 'user_id', 'label': _('Search in Assigned to'), 'sequence': 20},
            'reporter_id': {'input': 'reporter_id', 'label': _('Search in Reported by'), 'sequence': 30},
            'consolidated_status': {'input': 'consolidated_status', 'label': _('Search in Status'), 'sequence': 40},
            'classification': {'input': 'classification', 'label': _('Search in Classification'), 'sequence': 50},
        }

    def _ticket_get_searchbar_groupby(self):
        """ Remove the 'team_id', 'stage_id', and 'kanban_state' fields, add 'consolidated_status' and 'classification'. """
        return {
            'none': {'label': _('None'), 'sequence': 10},
            'user_id': {'label': _('Assigned to'), 'sequence': 20},
            'consolidated_status': {'label': _('Status'), 'sequence': 30},
            'classification': {'label': _('Classification'), 'sequence': 40},
            'reporter_id': {'label': _('Reported by'), 'sequence': 50},
        }

    # noinspection DuplicatedCode
    def _prepare_my_tickets_values(self, page=1, date_begin=None, date_end=None, sortby=None, filterby='all',
                                   search=None, groupby='none', search_in='name'):
        """ Override that removes 'stage_id' sort field and changes 'date_last_stage_update' to 'write_date'
        for the 'searchbar_sortings' option of the original method.
        Also makes sure that 'create_date' is replaced by 'ticket_date' wherever applicable.
        """
        values = self._prepare_portal_layout_values()
        domain = self._prepare_helpdesk_tickets_domain()

        searchbar_sortings = {
            'ticket_date desc': {'label': _('Newest')},
            'ticket_date asc': {'label': _('Oldest')},
            'display_ref desc': {'label': _('Reference')},
            'name': {'label': _('Subject')},
            'write_date desc': {'label': _('Last Update')},
        }
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'reporter_id': {'label': _('My Tickets'), 'domain': [('reporter_id', '=', http.request.env.user.id)]},
            'assigned': {'label': _('Assigned'), 'domain': [('user_id', '!=', False)]},
            'unassigned': {'label': _('Unassigned'), 'domain': [('user_id', '=', False)]},
            'open': {'label': _('Open'), 'domain': [('close_date', '=', False)]},
            'closed': {'label': _('Closed'), 'domain': [('close_date', '!=', False)]},
        }
        searchbar_inputs = dict(sorted(self._ticket_get_searchbar_inputs().items(), key=lambda item: item[1]['sequence']))
        searchbar_groupby = dict(sorted(self._ticket_get_searchbar_groupby().items(), key=lambda item: item[1]['sequence']))

        # default sort by value
        if not sortby:
            sortby = 'ticket_date desc'

        domain = expression.AND([domain, searchbar_filters[filterby]['domain']])

        if date_begin and date_end:
            domain = expression.AND([domain, [('ticket_date', '>', date_begin), ('ticket_date', '<=', date_end)]])

        # search
        if search and search_in:
            domain = expression.AND([domain, self._ticket_get_search_domain(search_in, search)])

        # pager
        tickets_count = http.request.env['helpdesk.ticket'].search_count(domain)
        pager = portal_pager(
            url="/my/tickets",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'search_in': search_in, 'search': search, 'groupby': groupby, 'filterby': filterby},
            total=tickets_count,
            page=page,
            step=self._items_per_page
        )

        order = f'{groupby}, {sortby}' if groupby != 'none' else sortby
        tickets = http.request.env['helpdesk.ticket'].search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        http.request.session['my_tickets_history'] = tickets.ids[:100]

        if not tickets:
            grouped_tickets = []
        elif groupby != 'none':
            # noinspection PyTypeChecker
            grouped_tickets = [http.request.env['helpdesk.ticket'].concat(*g) for k, g in groupbyelem(tickets, itemgetter(groupby))]
        else:
            grouped_tickets = [tickets]

        values.update({
            'date': date_begin,
            'grouped_tickets': grouped_tickets,
            'page_name': 'ticket',
            'default_url': '/my/tickets',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'searchbar_inputs': searchbar_inputs,
            'searchbar_groupby': searchbar_groupby,
            'sortby': sortby,
            'groupby': groupby,
            'search_in': search_in,
            'search': search,
            'filterby': filterby,
        })
        return values

    # Route overrides to make sure the user is always authenticated

    @http.route([
        '/my/ticket/<int:ticket_id>',
        "/helpdesk/ticket/<int:ticket_id>",
    ], type='http', auth="user", website=True)
    def tickets_followup(self, ticket_id=None, **kw):
        """ Override that makes sure the user is logged in. """
        return super().tickets_followup(ticket_id=ticket_id, **kw)

    @http.route([
        '/my/ticket/<int:ticket_id>/<access_token>',
        "/helpdesk/ticket/<int:ticket_id>/<access_token>",
    ], type='http', auth="public", website=True)
    def tickets_followup_with_token(self, ticket_id=None, access_token=None, **kw):
        return super().tickets_followup(ticket_id=ticket_id, access_token=access_token, **kw)

    @http.route([
        '/my/ticket/close/<int:ticket_id>'
    ], type='http', auth="user", website=True)
    def ticket_close(self, ticket_id=None, **kw):
        """ Override that makes sure the user is logged in. """
        return super().ticket_close(ticket_id=ticket_id, **kw)

    @http.route([
        '/my/ticket/close/<int:ticket_id>/<access_token>',
    ], type='http', auth="public", website=True)
    def ticket_close_with_token(self, ticket_id=None, access_token=None, **kw):
        return super().ticket_close(ticket_id=ticket_id, access_token=access_token, **kw)


class GeoCatWebsiteForm(WebsiteForm):

    @staticmethod
    def _looks_like_html(value):
        """ Check if the value looks like HTML by checking for angle brackets. """
        return bool(HTML_TAG_PATTERN.search(value))

    def html(self, field_label, field_input):
        """ Override to ensure that HTML content stays HTML (i.e. is not escaped) and that plain text is. """
        if field_label == 'description' and self._looks_like_html(field_input):
            # Quill wraps all paragraphs inside <p> tags and adds a blank line as <p><br></p>.
            # Odoo renders this with way too much line space, so it rather has double <br> tags.
            modified_input = field_input.replace('<p><br></p>', '<br>').replace('<p>', '').replace('</p>', '<br>').replace('\n', '')
            if modified_input.endswith('<br>'):
                # Remove trailing <br>
                modified_input = modified_input[:-len('<br>')]
            if not modified_input:
                # Raise ValueError to make sure user cannot submit an empty description
                return ValueError("Description cannot be empty.")
            return Markup(modified_input)
        else:
            # Use original plaintext2html for any other field, so that it is escaped properly
            return super().html(field_label, field_input)

    def __new__(cls, *more):
        """ Override to ensure that the custom html input filter is used. """
        # This is a workaround to ensure that our custom html input filter is used
        # instead of the default one from website_form.
        class_ = super(GeoCatWebsiteForm, cls).__new__(cls)
        class_._input_filters['html'] = cls.html
        return class_

    def insert_record(self, request, model, values, custom, meta=None):
        """ This override is an exact copy of the original method. We only want to override the h4 headers. """
        # Call super() on the original method to ensure that we bypass the insert_record from the website_helpdesk module
        res = super(WebsiteForm, self).insert_record(request, model, values, custom, meta=meta)
        if model.sudo().model != 'helpdesk.ticket':
            # If the model is not a helpdesk ticket, just return the result of the super call.
            return res

        # By default, portal users are not allowed to create helpdesk tickets and we keep it that way.
        # This means that the ticket is created by the superuser (bot) and not by the portal user.
        # However, we do want to set the reporter_id to the user ID associated with the partner ID,
        # so that the portal user sees that they created the ticket (even though create_uid is the bot).
        ticket = request.env['helpdesk.ticket'].sudo().browse(res)
        if ticket and ticket.reporter_id.id == ticket.create_uid.id == SUPERUSER_ID:
            ticket.write({'reporter_id': request.env.user.id})

        return res


class GeoCatHelpdesk(WebsiteHelpdesk):

    @http.route(['/my/ticket/new'], type='http', auth='user', website=True, sitemap=True)
    def website_new_ticket(self, **kwargs):
        """ Essentially the same as the website_helpdesk_teams method,
        but with different endpoint and assumes 1 (first) team. """
        teams_domain = [('use_website_helpdesk_form', '=', True)]
        if not http.request.env.user.has_group('helpdesk.group_helpdesk_manager'):
            teams_domain = expression.AND([teams_domain, [('website_published', '=', True)]])

        teams = http.request.env['helpdesk.team'].search(teams_domain, order="id asc")
        if not teams:
            raise NotFound()

        result = self.get_helpdesk_team_data(teams[0])
        result['multiple_teams'] = len(teams) > 1
        return http.request.render("website_helpdesk.team", result)

    # Make sure that our helpdesk route requires portal user authentication as well (i.e. not public)
    @http.route(['/helpdesk', '/helpdesk/<model("helpdesk.team"):team>'], type='http', auth='user', website=True,
                sitemap=False)
    def website_helpdesk_teams(self, team=None, **kwargs):
        return super().website_helpdesk_teams(team=team, **kwargs)

    def get_helpdesk_team_data(self, team, search=None):
        """ Override to add our custom ticket classifications so we can dynamically populate a selector. """
        return {
            'team': team,
            'main_object': team,
            'classifications': TICKET_CLASS,
            'default_classification': DEFAULT_CLASS,
        }
