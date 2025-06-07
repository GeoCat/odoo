# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestHelpdeskTicketCreate(TransactionCase):
    def setUp(self):
        super(TestHelpdeskTicketCreate, self).setUp()
        self.user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user',
        })
        self.reporter = self.env['res.users'].create({
            'name': 'Reporter',
            'login': 'test_reporter',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
        })
        self.team = self.env['helpdesk.team'].create({
            'name': 'Test Team',
        })

    def test_create_ticket(self):
        """Test the create() method of helpdesk.ticket."""
        ticket_data = {
            'name': 'Test Ticket',
            'partner_id': self.partner.id,
            'team_id': self.team.id,
        }
        ticket = self.env['helpdesk.ticket'].create(ticket_data)

        # Assert that the ticket was created successfully
        self.assertTrue(ticket.id, "Ticket was not created.")
        self.assertEqual(ticket.name, 'Test Ticket', "Ticket name mismatch.")
        self.assertEqual(ticket.partner_id.id, self.partner.id, "Partner mismatch.")
        self.assertEqual(ticket.team_id.id, self.team.id, "Team mismatch.")

        # Assert default values set by the overridden create() method
        self.assertEqual(ticket.ticket_date, ticket.create_date, "Ticket date mismatch.")
        self.assertEqual(ticket.reporter_id.id, ticket.create_uid.id, "Reporter mismatch.")

        ticket_data['name'] = 'Updated Test Ticket'
        ticket_data['ticket_date'] = '2023-10-01 12:00:00'
        ticket_data['reporter_id'] = self.reporter.id

        # Create a new ticket with the updated data
        ticket = self.env['helpdesk.ticket'].create(ticket_data)

        self.assertNotEqual(ticket.ticket_date, ticket.create_date, "Ticket date and create_date match.")
        self.assertNotEqual(ticket.reporter_id.id, ticket.create_uid.id, "Reporter matches create_uid.")
