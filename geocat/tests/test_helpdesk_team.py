from dateutil.relativedelta import relativedelta

from odoo.tests.common import TransactionCase
from odoo import fields


class TestHelpdeskTeamAutoCloseTickets(TransactionCase):

    def setUp(self):
        super(TestHelpdeskTeamAutoCloseTickets, self).setUp()

        # Create stages
        self.open_stage = self.env['helpdesk.stage'].create({'name': 'Open', 'fold': False})
        self.resolved_stage = self.env['helpdesk.stage'].create({'name': 'Resolved', 'fold': False})
        self.closed_stage = self.env['helpdesk.stage'].create({'name': 'Closed', 'fold': True})

        # Create a helpdesk team with auto-close settings
        self.team = self.env['helpdesk.team'].create({
            'name': 'Test Team',
            'auto_close_ticket': True,
            'auto_close_day': 7,
            'from_stage_ids': [self.resolved_stage.id],
            'to_stage_id': self.closed_stage.id,
            'use_website_helpdesk_form': True,
        })

        # Create blocked state for closed stage
        self.blocked_state = self.env['geocat.helpdesk.state'].create({
            'name': 'Blocked',
            'color': '#FF0000',
            'text_color': '#FFFFFF',
            'stage_id': self.closed_stage.id,
        })

        before_timeout = fields.Datetime.now() - relativedelta(days=5)
        after_timeout = fields.Datetime.now() - relativedelta(days=10)

        # Create tickets
        self.ticket_active1 = self.env['helpdesk.ticket'].create({
            'name': 'Open Ticket',
            'team_id': self.team.id,
            'stage_id': self.open_stage.id,
        })

        self.ticket_active2 = self.env['helpdesk.ticket'].create({
            'name': 'Open Ticket after Timeout',
            'team_id': self.team.id,
            'stage_id': self.open_stage.id,
        })

        self.ticket_active3 = self.env['helpdesk.ticket'].create({
            'name': 'Resolved Ticket before Timeout',
            'team_id': self.team.id,
            'stage_id': self.resolved_stage.id,
        })

        self.ticket_inactive = self.env['helpdesk.ticket'].create({
            'name': 'Resolved Ticket after Timeout',
            'team_id': self.team.id,
            'stage_id': self.resolved_stage.id,
        })

        self.ticket_blocked = self.env['helpdesk.ticket'].create({
            'name': 'Resolved Ticket (Blocked)',
            'team_id': self.team.id,
            'stage_id': self.resolved_stage.id,
            'blocked_state': self.blocked_state.id,
        })

        # As we cannot set write_date directly in create(), we need to update it manually using SQL
        self.env.cr.execute("""
            UPDATE helpdesk_ticket
            SET write_date = %s
            WHERE id IN %s
        """, (before_timeout, tuple(ticket.id for ticket in [self.ticket_active1, self.ticket_active3])))
        self.env.cr.execute("""
            UPDATE helpdesk_ticket
            SET write_date = %s
            WHERE id IN %s
        """, (after_timeout, tuple(ticket.id for ticket in [self.ticket_active2, self.ticket_inactive, self.ticket_blocked])))

        # Invalidate the cache so we are sure to run the tests on the updated write_date
        self.ticket_active1._invalidate_cache(['write_date'])
        self.ticket_active2._invalidate_cache(['write_date'])
        self.ticket_active3._invalidate_cache(['write_date'])
        self.ticket_inactive._invalidate_cache(['write_date'])
        self.ticket_blocked._invalidate_cache(['write_date'])

    def test_custom_ticket_form(self):
        """ Test that the custom ticket form view is applied correctly for the team. """
        # Get the custom form view for the team
        team_form = self.team.website_form_view_id

        # Check if the form view is set and has the correct arch
        self.assertTrue(team_form, "Website form view should be set for the team (if use_website_helpdesk_form is True).")
        self.assertIn('<input type="radio" name="classification" t-att-value="class_id" t-att-id="radio_id" t-att-checked="class_id == default_classification"/>', team_form.arch, "Custom form view should have classification input field.")

    def test_cron_auto_close_tickets(self):
        """Test the _cron_auto_close_tickets method."""
        self.team._cron_auto_close_tickets()

        # Assert active tickets remain in current their stage
        self.assertEqual(self.ticket_active1.stage_id, self.open_stage,
                         "Open ticket before timeout should remain in the open stage.")
        self.assertEqual(self.ticket_active2.stage_id, self.open_stage,
                         "Open ticket after timeout should remain in the open stage.")
        self.assertEqual(self.ticket_active3.stage_id, self.resolved_stage,
                         "Resolved ticket before timeout should remain in the resolved stage.")

        # Assert inactive resolved ticket is moved to the closed stage
        self.assertEqual(self.ticket_inactive.stage_id, self.closed_stage,
                         "Resolved ticket after timeout without blocked state should be moved to the closed stage.")

        # Assert blocked resolved ticket remains in the open stage
        self.assertEqual(self.ticket_blocked.stage_id, self.resolved_stage,
                         "Resolved ticket with blocked state should remain in the open stage.")
