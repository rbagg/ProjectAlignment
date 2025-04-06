# integrations/jira.py
import logging
import json
import random
from datetime import datetime

logger = logging.getLogger(__name__)

class JiraIntegration:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connected_projects = []
        self.tickets = [
            {
                'id': 'PROJ-1',
                'title': 'Implement document change detection',
                'description': 'Create a system that detects changes in connected documents.',
                'status': 'In Progress',
                'priority': 'High',
                'assignee': 'John Doe'
            },
            {
                'id': 'PROJ-2',
                'title': 'Build artifact generation engine',
                'description': 'Create a system that generates project descriptions and messaging.',
                'status': 'To Do',
                'priority': 'Medium',
                'assignee': 'Jane Smith'
            },
            {
                'id': 'PROJ-3',
                'title': 'Design minimalist UI',
                'description': 'Create a clean, text-focused interface for the application.',
                'status': 'Done',
                'priority': 'Low',
                'assignee': 'Alex Johnson'
            }
        ]

    def connect_project(self, project_id):
        """Mock connecting a Jira project"""
        self.connected_projects.append({
            'id': project_id,
            'connected_at': datetime.utcnow()
        })
        return True

    def get_tickets(self):
        """Mock getting tickets"""
        return self.tickets

    def get_ticket(self, ticket_id):
        """Mock getting a specific ticket"""
        for ticket in self.tickets:
            if ticket['id'] == ticket_id:
                return ticket
        return None