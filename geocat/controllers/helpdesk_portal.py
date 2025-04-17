from werkzeug.exceptions import NotFound
from operator import itemgetter
from markupsafe import Markup

from odoo import http, _
from odoo.osv import expression
from odoo.tools import groupby as groupbyelem, html2plaintext
from odoo.addons.base.models.ir_qweb_fields import nl2br, nl2br_enclose
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.addons.helpdesk.controllers.portal import CustomerPortal
from odoo.addons.website_helpdesk.controllers.main import WebsiteHelpdesk, WebsiteForm

from ..models.helpdesk_ticket import TICKET_CLASS, DEFAULT_CLASS


# noinspection DuplicatedCode
class GeoCatCustomerPortal(CustomerPortal):

    def _ticket_get_searchbar_inputs(self):
        return {
            'name': {'input': 'name', 'label': _(
                'Search%(left)s Tickets%(right)s',
                left=Markup('<span class="nolabel">'),
                right=Markup('</span>'),
            ), 'sequence': 10},
            'user_id': {'input': 'user_id', 'label': _('Search in Assigned to'), 'sequence': 20},
            'partner_id': {'input': 'partner_id', 'label': _('Search in Reporter'), 'sequence': 30},
        }

    def _ticket_get_searchbar_groupby(self):
        return {
            'none': {'label': _('None'), 'sequence': 10},
            'user_id': {'label': _('Assigned to'), 'sequence': 20},
            'consolidated_status': {'label': _('Status'), 'sequence': 30},
            'classification': {'label': _('Classification'), 'sequence': 40},
            'partner_id': {'label': _('Reporter'), 'sequence': 50},
        }

    def _ticket_get_search_domain(self, search_in, search):
        if search_in == 'name':
            return ['|', ('name', 'ilike', search), ('ticket_ref', 'ilike', search)]
        elif search_in == 'user_id':
            assignees = http.request.env['res.users'].sudo()._search([('name', 'ilike', search)])
            return [('user_id', 'in', assignees)]
        elif search_in in self._ticket_get_searchbar_inputs():
            return [(search_in, 'ilike', search)]
        else:
            return ['|', ('name', 'ilike', search), ('ticket_ref', 'ilike', search)]

    def _prepare_my_tickets_values(self, page=1, date_begin=None, date_end=None, sortby=None, filterby='all',
                                   search=None, groupby='none', search_in='name'):
        values = self._prepare_portal_layout_values()
        domain = self._prepare_helpdesk_tickets_domain()

        searchbar_sortings = {
            'create_date desc': {'label': _('Newest')},
            'id desc': {'label': _('Reference')},
            'name': {'label': _('Subject')},
            'user_id': {'label': _('Assigned to')},
            'write_date desc': {'label': _('Last Update')},
        }
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'assigned': {'label': _('Assigned'), 'domain': [('user_id', '!=', False)]},
            'unassigned': {'label': _('Unassigned'), 'domain': [('user_id', '=', False)]},
            'open': {'label': _('Open'), 'domain': [('close_date', '=', False)]},
            'closed': {'label': _('Closed'), 'domain': [('close_date', '!=', False)]},
        }
        searchbar_inputs = dict(
            sorted(self._ticket_get_searchbar_inputs().items(), key=lambda item: item[1]['sequence']))
        searchbar_groupby = dict(
            sorted(self._ticket_get_searchbar_groupby().items(), key=lambda item: item[1]['sequence']))

        # default sort by value
        if not sortby:
            sortby = 'create_date desc'

        domain = expression.AND([domain, searchbar_filters[filterby]['domain']])

        if date_begin and date_end:
            domain = expression.AND([domain, [('create_date', '>', date_begin), ('create_date', '<=', date_end)]])

        # search
        if search and search_in:
            domain = expression.AND([domain, self._ticket_get_search_domain(search_in, search)])

        # pager
        tickets_count = http.request.env['helpdesk.ticket'].search_count(domain)
        pager = portal_pager(
            url="/my/tickets",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'search_in': search_in,
                      'search': search, 'groupby': groupby, 'filterby': filterby},
            total=tickets_count,
            page=page,
            step=self._items_per_page
        )

        order = f'{groupby}, {sortby}' if groupby != 'none' else sortby
        tickets = http.request.env['helpdesk.ticket'].search(domain, order=order, limit=self._items_per_page,
                                                        offset=pager['offset'])
        http.request.session['my_tickets_history'] = tickets.ids[:100]

        if not tickets:
            grouped_tickets = []
        elif groupby != 'none':
            grouped_tickets = [http.request.env['helpdesk.ticket'].concat(*g) for k, g in
                               groupbyelem(tickets, itemgetter(groupby))]
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

    # noinspection DuplicatedCode
    def insert_record(self, request, model, values, custom, meta=None):
        """ This override is an exact copy of the original method. We only want to override the h4 headers. """
        res = super().insert_record(request, model, values, custom, meta=meta)
        if model.sudo().model != 'helpdesk.ticket':
            return res
        ticket = request.env['helpdesk.ticket'].sudo().browse(res)
        custom_label = nl2br_enclose(_("Other Information"), 'h6')  # Title for custom fields
        default_field = model.website_form_default_field_id  # Typically the description field
        default_field_data = values.get(default_field.name, '')
        default_field_content = nl2br_enclose(html2plaintext(default_field_data), 'p')
        custom_content = ((default_field_content if default_field_data else '')
                          + (custom_label + custom if custom else '')
                          + (self._meta_label + meta if meta else ''))

        if default_field.name:
            if default_field.ttype == 'html':
                custom_content = nl2br(custom_content)
            ticket[default_field.name] = custom_content
            ticket._message_log(
                body=custom_content,
                message_type='comment',
            )
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
