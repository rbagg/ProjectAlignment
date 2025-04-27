# services/alignment_service.py
import json
import logging
from datetime import datetime
from models import db, Alignment, Project
from flask import current_app
import anthropic

logger = logging.getLogger(__name__)

class AlignmentService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_suggestions(self):
        """Get the latest alignment suggestions"""
        alignment = Alignment.query.order_by(Alignment.timestamp.desc()).first()
        if alignment:
            return alignment.get_suggestions_list()
        return []

    def analyze_changes(self, current_content):
        """
        Analyze changes between the current content and the most recent project

        Args:
            current_content (str): JSON string of current project content

        Returns:
            dict: Changes detected between previous and current content
        """
        # Get the most recent project
        previous_project = Project.query.order_by(Project.timestamp.desc()).first()

        # If no previous project, everything is new
        if not previous_project:
            return self._all_new_changes(current_content)

        # Parse JSON content
        current = json.loads(current_content)
        previous = previous_project.get_content_dict()

        # Track changes by type
        changes = {
            'prd': self._compare_documents(previous.get('prd', {}), current.get('prd', {})),
            'prfaq': self._compare_documents(previous.get('prfaq', {}), current.get('prfaq', {})),
            'tickets': self._compare_tickets(previous.get('tickets', []), current.get('tickets', [])),
            'strategy': self._compare_documents(previous.get('strategy', {}), current.get('strategy', {}))
        }

        return changes

    def format_suggestions(self, changes):
        """
        Format changes into actionable suggestions using Claude

        Args:
            changes (dict): Changes detected in project content

        Returns:
            str: JSON string of formatted suggestions
        """
        # If there are no significant changes, use rule-based generation
        if not self._has_significant_changes(changes):
            return self._rule_based_suggestions(changes)

        # Initialize Claude client
        try:
            api_key = current_app.config.get('CLAUDE_API_KEY')
            model = current_app.config.get('CLAUDE_MODEL', 'claude-3-opus-20240229')
            client = anthropic.Anthropic(api_key=api_key)  # Make sure no extra parameters are here
        except Exception as e:
            self.logger.error(f"Error initializing Claude client: {str(e)}")
            # Fall back to rule-based generation if Claude is unavailable
            return self._rule_based_suggestions(changes)

        # Format changes for Claude
        changes_formatted = json.dumps(changes, indent=2)

        # Create prompt for Claude
        prompt = f"""
        I need to generate suggestions for keeping project documents aligned based on detected changes.

        The following changes have been detected in various project documents:

        {changes_formatted}

        Please generate actionable suggestions for what needs to be updated to keep everything aligned.
        For example, if the PRD changed, suggest updates to tickets. If tickets changed, suggest updates to the PRD.

        Format the response as a JSON array of suggestion objects, each with the following structure:
        {{
            "type": "[source]_to_[target]",
            "action": "create|update|review|remove",
            "description": "Clear description of what needs to be done",
            "source": "Which document triggered this suggestion",
            "target": "Which document needs to be updated"
        }}

        Example format:
        [
            {{
                "type": "prd_to_tickets",
                "action": "create",
                "description": "Create tickets for new feature X described in PRD",
                "source": "prd",
                "target": "tickets"
            }}
        ]

        Focus on the most important alignments needed, providing specific and actionable suggestions.
        """

        try:
            # Call Claude
            response = client.messages.create(
                model=model,
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract and parse the response
            response_text = response.content[0].text

            # Find JSON in the response
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1

            if json_start != -1 and json_end != -1:
                json_str = response_text[json_start:json_end]
                return json_str
            else:
                self.logger.error("Could not find JSON in Claude response")
                return self._rule_based_suggestions(changes)

        except Exception as e:
            self.logger.error(f"Error generating suggestions with Claude: {str(e)}")
            # Fall back to rule-based generation
            return self._rule_based_suggestions(changes)

    def _has_significant_changes(self, changes):
        """Check if there are significant changes that warrant Claude analysis"""
        total_changes = 0

        for doc_type, doc_changes in changes.items():
            total_changes += len(doc_changes.get('added', []))
            total_changes += len(doc_changes.get('modified', []))
            total_changes += len(doc_changes.get('removed', []))

        return total_changes > 0

    def _all_new_changes(self, content_json):
        """Create a changes dict when everything is new"""
        content = json.loads(content_json)
        changes = {}

        # Mark everything as added
        for key, value in content.items():
            if key == 'tickets':
                changes[key] = {
                    'added': [ticket['id'] for ticket in value],
                    'modified': [],
                    'removed': []
                }
            else:
                changes[key] = {
                    'added': list(value.keys()) if isinstance(value, dict) else ['all'],
                    'modified': [],
                    'removed': []
                }

        return changes

    def _compare_documents(self, previous, current):
        """
        Compare previous and current document content to identify changes

        Args:
            previous (dict): Previous document content by section
            current (dict): Current document content by section

        Returns:
            dict: Contains added, modified, and removed sections
        """
        # Track changes
        changes = {
            'added': [],
            'modified': [],
            'removed': []
        }

        # Find added and modified sections
        for section, content in current.items():
            if section not in previous:
                changes['added'].append(section)
            elif previous[section] != content:
                changes['modified'].append(section)

        # Find removed sections
        for section in previous:
            if section not in current:
                changes['removed'].append(section)

        return changes

    def _compare_tickets(self, previous_tickets, current_tickets):
        """
        Compare previous and current tickets to identify changes

        Args:
            previous_tickets (list): List of previous ticket dictionaries
            current_tickets (list): List of current ticket dictionaries

        Returns:
            dict: Contains added, modified, and removed ticket IDs
        """
        # Create ID-based lookups for easier comparison
        prev_by_id = {ticket['id']: ticket for ticket in previous_tickets}
        curr_by_id = {ticket['id']: ticket for ticket in current_tickets}

        # Track changes
        changes = {
            'added': [],
            'modified': [],
            'removed': []
        }

        # Find added and modified tickets
        for ticket_id, ticket in curr_by_id.items():
            if ticket_id not in prev_by_id:
                changes['added'].append(ticket_id)
            elif prev_by_id[ticket_id] != ticket:
                changes['modified'].append(ticket_id)

        # Find removed tickets
        for ticket_id in prev_by_id:
            if ticket_id not in curr_by_id:
                changes['removed'].append(ticket_id)

        return changes

    def _rule_based_suggestions(self, changes):
        """
        Format changes into actionable suggestions (rule-based approach)

        Args:
            changes (dict): Changes detected in project content

        Returns:
            str: JSON string of formatted suggestions
        """
        suggestions = []

        # Suggestions for PRD changes
        prd_changes = changes.get('prd', {})
        if prd_changes['added'] or prd_changes['modified'] or prd_changes['removed']:
            # Add suggestions to update tickets based on PRD changes
            for section in prd_changes.get('added', []):
                suggestions.append({
                    'type': 'prd_to_tickets',
                    'action': 'create',
                    'description': f"Consider creating tickets for new PRD section: '{section}'",
                    'source': 'prd',
                    'target': 'tickets'
                })

            for section in prd_changes.get('modified', []):
                suggestions.append({
                    'type': 'prd_to_tickets',
                    'action': 'update',
                    'description': f"Review tickets related to modified PRD section: '{section}'",
                    'source': 'prd',
                    'target': 'tickets'
                })

            for section in prd_changes.get('removed', []):
                suggestions.append({
                    'type': 'prd_to_tickets',
                    'action': 'remove',
                    'description': f"Consider closing tickets related to removed PRD section: '{section}'",
                    'source': 'prd',
                    'target': 'tickets'
                })

        # Suggestions for ticket changes
        ticket_changes = changes.get('tickets', {})
        if ticket_changes['added'] or ticket_changes['modified'] or ticket_changes['removed']:
            # Add suggestions to update PRD based on ticket changes
            if ticket_changes.get('added', []):
                suggestions.append({
                    'type': 'tickets_to_prd',
                    'action': 'update',
                    'description': f"Update PRD to include {len(ticket_changes['added'])} new tickets",
                    'source': 'tickets',
                    'target': 'prd'
                })

            if ticket_changes.get('modified', []):
                suggestions.append({
                    'type': 'tickets_to_prd',
                    'action': 'update',
                    'description': f"Review PRD sections related to {len(ticket_changes['modified'])} modified tickets",
                    'source': 'tickets',
                    'target': 'prd'
                })

        # Suggestions for PRFAQ changes
        prfaq_changes = changes.get('prfaq', {})
        if prfaq_changes['added'] or prfaq_changes['modified'] or prfaq_changes['removed']:
            suggestions.append({
                'type': 'prfaq_alignment',
                'action': 'review',
                'description': "Ensure PRD and PRFAQ remain aligned after recent changes",
                'source': 'prfaq',
                'target': 'prd'
            })

        # Suggestions for strategy changes
        strategy_changes = changes.get('strategy', {})
        if strategy_changes['added'] or strategy_changes['modified'] or strategy_changes['removed']:
            suggestions.append({
                'type': 'strategy_alignment',
                'action': 'review',
                'description': "Review PRD and tickets to ensure alignment with updated strategy",
                'source': 'strategy',
                'target': 'all'
            })

        return json.dumps(suggestions)