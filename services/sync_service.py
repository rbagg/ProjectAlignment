# services/sync_service.py
import json
import logging
from datetime import datetime

from models import db, Project

logger = logging.getLogger(__name__)

class SyncService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Store references to integration instances (will be set by main.py)
        self.google_docs = None
        self.jira = None
        self.linear = None
        self.confluence = None

    def set_integrations(self, google_docs, jira, linear, confluence):
        """Set integration instances"""
        self.google_docs = google_docs
        self.jira = jira
        self.linear = linear
        self.confluence = confluence

    def collect_all_content(self):
        """
        Collect content from all connected documents

        Returns:
            str: JSON string of all project content
        """
        content = {
            'prd': {},
            'prfaq': {},
            'strategy': {},
            'tickets': []
        }

        # Collect Google Docs content
        if self.google_docs:
            docs = self.google_docs.get_connected_docs()
            for doc in docs:
                if doc['type'] == 'prd':
                    content['prd'] = self.google_docs.get_document_content(doc['id'])
                elif doc['type'] == 'prfaq':
                    content['prfaq'] = self.google_docs.get_document_content(doc['id'])
                elif doc['type'] == 'strategy':
                    content['strategy'] = self.google_docs.get_document_content(doc['id'])

        # Collect Jira tickets
        if self.jira:
            content['tickets'].extend(self.jira.get_tickets())

        # Collect Linear tickets
        if self.linear:
            content['tickets'].extend(self.linear.get_tickets())

        # Additional content from Confluence
        if self.confluence:
            confluence_content = self.confluence.get_pages()
            # Merge with appropriate sections based on page labels or metadata
            for page in confluence_content:
                if 'prd' in page.get('labels', []):
                    self._merge_content(content['prd'], page['content'])
                elif 'strategy' in page.get('labels', []):
                    self._merge_content(content['strategy'], page['content'])

        return json.dumps(content)

    def _merge_content(self, target, source):
        """Merge source content into target"""
        if isinstance(source, dict) and isinstance(target, dict):
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    self._merge_content(target[key], value)
                else:
                    target[key] = value

    def handle_jira_update(self, data):
        """
        Handle updates from Jira

        Args:
            data (dict): Webhook payload from Jira

        Returns:
            dict: Changes detected, if any
        """
        # Process Jira webhook data
        issue_key = data.get('issue', {}).get('key')
        if not issue_key:
            return None

        # Get the latest project
        latest_project = Project.query.order_by(Project.timestamp.desc()).first()
        if not latest_project:
            return None

        content = latest_project.get_content_dict()

        # Find the ticket in current content
        tickets = content.get('tickets', [])
        existing_ticket_idx = next((i for i, t in enumerate(tickets) if t.get('id') == issue_key), None)

        # Get updated ticket data
        updated_ticket = self.jira.get_ticket(issue_key)

        # Determine if this is a new, updated, or deleted ticket
        changes = {
            'tickets': {
                'added': [],
                'modified': [],
                'removed': []
            }
        }

        if data.get('webhookEvent') == 'jira:issue_deleted':
            if existing_ticket_idx is not None:
                tickets.pop(existing_ticket_idx)
                changes['tickets']['removed'].append(issue_key)
        elif existing_ticket_idx is None:
            # New ticket
            tickets.append(updated_ticket)
            changes['tickets']['added'].append(issue_key)
        else:
            # Updated ticket
            old_ticket = tickets[existing_ticket_idx]
            tickets[existing_ticket_idx] = updated_ticket

            # Check if there were meaningful changes
            if self._tickets_differ(old_ticket, updated_ticket):
                changes['tickets']['modified'].append(issue_key)
            else:
                # No meaningful changes
                return None

        # Update content and save
        content['tickets'] = tickets

        return changes if any(len(c) > 0 for c in changes['tickets'].values()) else None

    def handle_docs_update(self, data):
        """
        Handle updates from Google Docs

        Args:
            data (dict): Webhook payload from Google Docs

        Returns:
            dict: Changes detected, if any
        """
        # Process Google Docs webhook data
        doc_id = data.get('documentId')
        if not doc_id:
            return None

        # Get the latest project
        latest_project = Project.query.order_by(Project.timestamp.desc()).first()
        if not latest_project:
            return None

        content = latest_project.get_content_dict()

        # Get document type and current content
        doc_type = self.google_docs.get_document_type(doc_id)
        if not doc_type:
            return None

        # Get updated document content
        updated_content = self.google_docs.get_document_content(doc_id)

        # Initialize changes
        changes = {
            doc_type: {
                'added': [],
                'modified': [],
                'removed': []
            }
        }

        # Compare with current content
        current_content = content.get(doc_type, {})

        # Find added sections
        for section, text in updated_content.items():
            if section not in current_content:
                changes[doc_type]['added'].append(section)
            elif current_content[section] != text:
                changes[doc_type]['modified'].append(section)

        # Find removed sections
        for section in current_content:
            if section not in updated_content:
                changes[doc_type]['removed'].append(section)

        # Update content
        content[doc_type] = updated_content

        return changes if any(len(c) > 0 for c in changes[doc_type].values()) else None

    def handle_confluence_update(self, data):
        """
        Handle updates from Confluence

        Args:
            data (dict): Webhook payload from Confluence

        Returns:
            dict: Changes detected, if any
        """
        # Process Confluence webhook data
        page_id = data.get('page', {}).get('id')
        if not page_id:
            return None

        # Get the latest project
        latest_project = Project.query.order_by(Project.timestamp.desc()).first()
        if not latest_project:
            return None

        content = latest_project.get_content_dict()

        # Get page information and content
        page = self.confluence.get_page(page_id)
        if not page:
            return None

        # Determine which content section this belongs to based on labels
        doc_type = None
        if 'prd' in page.get('labels', []):
            doc_type = 'prd'
        elif 'strategy' in page.get('labels', []):
            doc_type = 'strategy'
        else:
            return None

        # Initialize changes
        changes = {
            doc_type: {
                'added': [],
                'modified': [],
                'removed': []
            }
        }

        # Extract structured content sections
        page_content = self.confluence.extract_structured_content(page)

        # Compare with current content
        current_content = content.get(doc_type, {})

        # Find added and modified sections
        for section, text in page_content.items():
            if section not in current_content:
                changes[doc_type]['added'].append(section)
                current_content[section] = text
            elif current_content[section] != text:
                changes[doc_type]['modified'].append(section)
                current_content[section] = text

        # Update content
        content[doc_type] = current_content

        return changes if any(len(c) > 0 for c in changes[doc_type].values()) else None

    def _tickets_differ(self, ticket1, ticket2):
        """
        Check if two tickets have meaningful differences

        Args:
            ticket1 (dict): First ticket
            ticket2 (dict): Second ticket

        Returns:
            bool: True if tickets have meaningful differences
        """
        # Fields that indicate meaningful changes
        important_fields = ['title', 'description', 'status', 'priority', 'assignee']

        for field in important_fields:
            if ticket1.get(field) != ticket2.get(field):
                return True

        return False

    def handle_linear_update(self, data):
        """
        Handle updates from Linear

        Args:
            data (dict): Webhook payload from Linear

        Returns:
            dict: Changes detected, if any
        """
        # Process Linear webhook data
        issue_id = data.get('data', {}).get('id')
        action = data.get('action')

        if not issue_id or not action:
            return None

        # Get the latest project
        latest_project = Project.query.order_by(Project.timestamp.desc()).first()
        if not latest_project:
            return None

        content = latest_project.get_content_dict()

        # Find the ticket in current content
        tickets = content.get('tickets', [])
        existing_ticket_idx = next((i for i, t in enumerate(tickets) if t.get('id') == issue_id), None)

        # Initialize changes
        changes = {
            'tickets': {
                'added': [],
                'modified': [],
                'removed': []
            }
        }

        if action == 'remove':
            if existing_ticket_idx is not None:
                tickets.pop(existing_ticket_idx)
                changes['tickets']['removed'].append(issue_id)
        elif action == 'create':
            # New ticket
            updated_ticket = self.linear.get_ticket(issue_id)
            tickets.append(updated_ticket)
            changes['tickets']['added'].append(issue_id)
        elif action == 'update':
            # Updated ticket
            updated_ticket = self.linear.get_ticket(issue_id)
            if existing_ticket_idx is not None:
                old_ticket = tickets[existing_ticket_idx]
                tickets[existing_ticket_idx] = updated_ticket

                # Check if there were meaningful changes
                if self._tickets_differ(old_ticket, updated_ticket):
                    changes['tickets']['modified'].append(issue_id)
                else:
                    # No meaningful changes
                    return None

        # Update content and save
        content['tickets'] = tickets

        return changes if any(len(c) > 0 for c in changes['tickets'].values()) else None