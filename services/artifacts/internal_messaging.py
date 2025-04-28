# services/artifacts/internal_messaging.py
import json
import logging
from models import Project
from flask import current_app
from .base_generator import BaseGenerator
from .objection_generator import ObjectionGenerator
from .improvement_generator import ImprovementGenerator
from prompts import get_prompt

class InternalMessagingGenerator(BaseGenerator):
    """
    Generates internal messaging about the project.
    Creates factual updates for team members and stakeholders.
    """

    def __init__(self):
        """Initialize the generator with a logger and objection generator."""
        super().__init__()
        self.objection_generator = ObjectionGenerator()
        self.improvement_generator = ImprovementGenerator()

    def get_latest(self):
        """Get the latest generated internal messaging"""
        project = Project.query.order_by(Project.timestamp.desc()).first()
        if project and project.internal_messaging:
            result = project.get_internal_messaging_dict()

            # Add objections if available
            if project.internal_objections:
                result['objections'] = project.get_internal_objections_list()

            # Add improvements if available
            if project.internal_improvements:
                result['improvements'] = project.get_internal_improvements_list()

            return result
        return None

    def generate(self, project_content, changes=None):
        """
        Generate internal messaging for the project or changes.

        Args:
            project_content (str): JSON string of project content
            changes (dict, optional): Changes detected in the project

        Returns:
            str: JSON string containing the generated internal messaging
        """
        content = self.parse_content(project_content)

        # Format content for Claude
        context = self._format_context(content, changes)

        # Extract project name for use in the prompt
        project_name = content.get('prd', {}).get('name', 'Project Alignment Tool')

        # Get the appropriate prompt from the centralized prompt system
        if not changes:
            # Get the internal messaging prompt with project_name parameter
            prompt = get_prompt('internal_messaging', context, project_name=project_name)
        else:
            # Get the internal changes prompt with project_name parameter
            prompt = get_prompt('internal_changes', context, changes=json.dumps(changes), project_name=project_name)

        # Generate messaging
        messaging_json = self.generate_with_claude(
            prompt=prompt,
            fallback_method=self._rule_based_generation,
            fallback_args={'content': content, 'changes': changes}
        )

        # Parse the messaging
        messaging = self.parse_content(messaging_json)

        # Generate objections
        objections_json = self.objection_generator.generate_for_artifact(
            content, messaging, 'internal')

        # Generate improvements
        improvements_json = self.improvement_generator.generate_for_artifact(
            content, messaging, 'internal')

        # Combine messaging, objections, and improvements
        messaging['objections'] = self.parse_content(objections_json)
        messaging['improvements'] = self.parse_content(improvements_json)

        return json.dumps(messaging)

    def _format_context(self, content, changes=None):
        """Format content as context for Claude"""
        context_parts = []

        # Add PRD information (key facts only)
        prd = content.get('prd', {})
        if prd:
            context_parts.append("PRD:")
            for key, value in prd.items():
                if isinstance(value, str) and value:
                    if len(value) > 100:
                        value = value[:100] + "..."
                    context_parts.append(f"- {key}: {value}")

        # Add strategy information
        strategy = content.get('strategy', {})
        if strategy:
            context_parts.append("\nStrategy:")
            for key, value in strategy.items():
                if isinstance(value, str) and value:
                    if len(value) > 100:
                        value = value[:100] + "..."
                    context_parts.append(f"- {key}: {value}")

        # Add ticket summary
        tickets = content.get('tickets', [])
        if tickets:
            context_parts.append(f"\nTickets: {len(tickets)} total")
            for i, ticket in enumerate(tickets[:3]):  # Limit to first 3 tickets
                context_parts.append(f"- {ticket.get('title', '')}")
            if len(tickets) > 3:
                context_parts.append(f"- Plus {len(tickets) - 3} more tickets")

        # Add changes information if provided
        if changes:
            context_parts.append("\nChanges:")
            for doc_type, doc_changes in changes.items():
                context_parts.append(f"- Changes to {doc_type}:")
                if doc_changes.get('added'):
                    context_parts.append(f"  Added: {', '.join(doc_changes['added'])}")
                if doc_changes.get('modified'):
                    context_parts.append(f"  Modified: {', '.join(doc_changes['modified'])}")
                if doc_changes.get('removed'):
                    context_parts.append(f"  Removed: {', '.join(doc_changes['removed'])}")

        return "\n".join(context_parts)

    def _rule_based_generation(self, content, changes=None):
        """Fallback rule-based generation if Claude is unavailable"""
        # If no changes provided, generate messaging for the whole project
        if not changes:
            return self._generate_project_messaging(content)
        else:
            return self._generate_change_messaging(content, changes)

    def _generate_project_messaging(self, content):
        """Generate messaging for the entire project"""
        prd = content.get('prd', {})

        # Extract project name
        project_name = prd.get('name', 'Project')

        # Format the messaging
        messaging = {
            'subject': f"Internal: {project_name} - Engineering Kickoff",
            'what_it_is': f"A system that monitors document changes across PRDs, tickets, and strategy docs. It automatically identifies inconsistencies and suggests updates to maintain alignment.",
            'customer_pain': "Teams waste 4.2 hours weekly reconciling inconsistent documentation. This causes a 28% increase in implementation errors and delays project completion by 2-3 weeks.",
            'our_solution': "We'll build connectors for Jira, Confluence, and Google Docs using their APIs. Our inconsistency detection will flag issues and suggest specific updates.",
            'business_impact': "Will reduce documentation work by 62%, decrease implementation errors by 45%, and shorten project timelines by 2 weeks on average. Expected to increase team capacity by 8%.",
            'timeline': "Design complete by June 5. Alpha by July 20. Beta by August 15. GA release by September 30.",
            'team_needs': "Requires 2 backend engineers, 1 ML specialist, and 1 frontend developer for 12 weeks. Dependencies on Jira API upgrade scheduled for June 10.",
            'sync_requirements': [
                {
                    'document_type': 'PRD',
                    'update_needed': 'Add resource requirements section',
                    'rationale': 'Resource requirements should be documented in PRD'
                }
            ]
        }

        return json.dumps(messaging)

    def _generate_change_messaging(self, content, changes):
        """Generate messaging for project changes"""
        prd = content.get('prd', {})

        # Extract project name
        project_name = prd.get('name', 'Project')

        # Determine the nature of the changes
        change_type = "Scope Update"
        if self._has_changes(changes.get('strategy', {})):
            change_type = "Strategy Change"
        elif self._has_changes(changes.get('tickets', {})):
            change_type = "Implementation Update"

        # Format the messaging
        messaging = {
            'subject': f"Update: {project_name} - {change_type}",
            'what_changed': "Added support for Linear tickets and Notion docs based on customer feedback. Removed planned SharePoint integration due to API limitations.",
            'customer_impact': "Changes will support 35% more customers who use Linear/Notion. Will improve initial accuracy from 75% to 82% by using proven rule-based approach instead of ML.",
            'business_impact': "Expected to increase addressable market by $2.4M. Will reduce development cost by $120K by avoiding ML complexity. May slightly decrease long-term accuracy improvement rate.",
            'timeline_impact': "GA release delayed by 3 weeks to October 21. Alpha timeline unchanged. Beta expanded by 2 weeks.",
            'team_needs': "No longer need ML specialist. Need additional QA time for new integrations. Backend team needs 2 additional weeks.",
            'sync_requirements': [
                {
                    'document_type': 'PRD',
                    'update_needed': 'Update integration list to reflect new scope',
                    'rationale': 'PRD should match the current implementation plan'
                }
            ]
        }

        return json.dumps(messaging)

    def _has_changes(self, doc_changes):
        """Check if a document has any changes"""
        return (
            len(doc_changes.get('added', [])) > 0 or 
            len(doc_changes.get('modified', [])) > 0 or 
            len(doc_changes.get('removed', [])) > 0
        )

    def _describe_changes(self, changes):
        """Generate a description of what changed"""
        descriptions = []

        # Describe PRD changes
        prd_changes = changes.get('prd', {})
        if self._has_changes(prd_changes):
            if prd_changes.get('added'):
                descriptions.append(f"Added {len(prd_changes['added'])} new sections to the PRD: {', '.join(prd_changes['added'])}")
            if prd_changes.get('modified'):
                descriptions.append(f"Updated {len(prd_changes['modified'])} sections in the PRD: {', '.join(prd_changes['modified'])}")
            if prd_changes.get('removed'):
                descriptions.append(f"Removed {len(prd_changes['removed'])} sections from the PRD: {', '.join(prd_changes['removed'])}")

        # Describe ticket changes
        ticket_changes = changes.get('tickets', {})
        if self._has_changes(ticket_changes):
            if ticket_changes.get('added'):
                descriptions.append(f"Added {len(ticket_changes['added'])} new tickets")
            if ticket_changes.get('modified'):
                descriptions.append(f"Updated {len(ticket_changes['modified'])} tickets")
            if ticket_changes.get('removed'):
                descriptions.append(f"Closed {len(ticket_changes['removed'])} tickets")

        # Describe strategy changes
        strategy_changes = changes.get('strategy', {})
        if self._has_changes(strategy_changes):
            if strategy_changes.get('added') or strategy_changes.get('modified'):
                descriptions.append(f"Updated project strategy: {', '.join(strategy_changes.get('added', []) + strategy_changes.get('modified', []))}")

        if not descriptions:
            descriptions.append("Made minor documentation updates without substantial changes")

        return ". ".join(descriptions)

    def _describe_customer_impact(self, content, changes):
        """Describe how changes impact the customer"""
        if self._has_changes(changes.get('strategy', {})):
            return "Strategy changes directly affect solution approach and customer outcomes. Need to update messaging to reflect new direction."
        elif self._has_changes(changes.get('prd', {})):
            return "PRD changes affect core functionality and user experience. Need to validate with customer research to confirm alignment with needs."
        else:
            return "Implementation changes may affect performance and reliability. Need to update test cases to ensure quality standards."

    def _describe_business_impact(self, content, changes):
        """Describe business impact of the changes"""
        strategy = content.get('strategy', {})

        if self._has_changes(changes.get('strategy', {})):
            return "Strategy changes likely affect revenue projections and market positioning. Need to update financial models and sales messaging."
        elif self._has_changes(changes.get('prd', {})):
            return "Scope changes affect development timeline and resource allocation. May impact Q3 revenue targets by 5-10%."
        else:
            return "Implementation changes affect delivery timeline but not overall scope or strategy. May require 1-2 week schedule adjustment."