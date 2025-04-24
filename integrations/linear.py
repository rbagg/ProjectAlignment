# integrations/linear.py
import logging
import json
import random
from datetime import datetime

logger = logging.getLogger(__name__)

class LinearIntegration:
    """
    Integration with Linear task management platform.

    This class provides methods to connect to Linear, retrieve tickets,
    and handle Linear webhook events.
    """

    def __init__(self):
        """Initialize the Linear integration with mock data."""
        self.logger = logging.getLogger(__name__)
        self.connected_projects = []
        self.tickets = [
            {
                'id': 'LIN-1',
                'title': 'Implement document sync mechanism',
                'description': 'Create a bidirectional sync system that keeps documents in sync.',
                'status': 'In Progress',
                'priority': 'High',
                'assignee': 'Jamie Wong'
            },
            {
                'id': 'LIN-2',
                'title': 'Create objection generation system',
                'description': 'Build a system that generates thoughtful objections to challenge user thinking.',
                'status': 'To Do',
                'priority': 'High',
                'assignee': 'Alex Johnson'
            },
            {
                'id': 'LIN-3',
                'title': 'Design improved UI for objections',
                'description': 'Create a clean interface for displaying objections in a constructive manner.',
                'status': 'To Do',
                'priority': 'Medium',
                'assignee': 'Taylor Swift'
            }
        ]

    def connect_project(self, project_id):
        """
        Connect to a Linear project.

        Args:
            project_id (str): The Linear project ID to connect

        Returns:
            bool: True if connection was successful
        """
        self.connected_projects.append({
            'id': project_id,
            'connected_at': datetime.utcnow()
        })
        return True

    def get_tickets(self):
        """
        Get tickets from the connected Linear project.

        Returns:
            list: List of ticket dictionaries
        """
        return self.tickets

    def get_ticket(self, ticket_id):
        """
        Get a specific ticket by ID.

        Args:
            ticket_id (str): The ticket ID to retrieve

        Returns:
            dict: Ticket data or None if not found
        """
        for ticket in self.tickets:
            if ticket['id'] == ticket_id:
                return ticket
        return None

    def create_ticket(self, title, description, priority='Medium'):
        """
        Create a new ticket in Linear.

        Args:
            title (str): Ticket title
            description (str): Ticket description
            priority (str): Ticket priority (Low, Medium, High)

        Returns:
            dict: The created ticket
        """
        # Generate a new ID
        max_id = max([int(t['id'].split('-')[1]) for t in self.tickets])
        new_id = f"LIN-{max_id + 1}"

        # Create the ticket
        ticket = {
            'id': new_id,
            'title': title,
            'description': description,
            'status': 'To Do',
            'priority': priority,
            'assignee': None
        }

        self.tickets.append(ticket)
        return ticket