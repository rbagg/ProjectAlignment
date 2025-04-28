# services/artifacts/external_messaging.py
import json
import logging
from models import Project
from flask import current_app
from .base_generator import BaseGenerator
from .objection_generator import ObjectionGenerator
from .improvement_generator import ImprovementGenerator
from prompts import get_prompt

class ExternalMessagingGenerator(BaseGenerator):
    """
    Generates external messaging about the project.
    Creates factual customer-facing messaging.
    """

    def __init__(self):
        """Initialize the generator with a logger, objection generator, and improvement generator."""
        super().__init__()
        self.objection_generator = ObjectionGenerator()
        self.improvement_generator = ImprovementGenerator()

    def get_latest(self):
        """Get the latest generated external messaging"""
        project = Project.query.order_by(Project.timestamp.desc()).first()
        if project and project.external_messaging:
            result = project.get_external_messaging_dict()

            # Add objections if available
            if project.external_objections:
                result['objections'] = project.get_external_objections_list()

            # Add improvements if available
            if project.external_improvements:
                result['improvements'] = project.get_external_improvements_list()

            return result
        return None

    def generate(self, project_content, changes=None):
        """
        Generate external messaging for the project or changes.

        Args:
            project_content (str): JSON string of project content
            changes (dict, optional): Changes detected in the project

        Returns:
            str: JSON string containing the generated external messaging
        """
        content = self.parse_content(project_content)

        # Format content for Claude
        context = self._format_context(content, changes)

        # Extract project name for use in the prompt (needed for changes prompt)
        project_name = content.get('prd', {}).get('name', 'Project Alignment Tool')

        # Get the appropriate prompt from the centralized prompt system
        if not changes:
            # Get the external messaging prompt
            prompt = get_prompt('external_messaging', context)
        else:
            # Get the external changes prompt with project_name parameter
            prompt = get_prompt('external_changes', context, changes=json.dumps(changes), project_name=project_name)

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
            content, messaging, 'external')

        # Generate improvements
        improvements_json = self.improvement_generator.generate_for_artifact(
            content, messaging, 'external')

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

        # Add PRFAQ highlights
        prfaq = content.get('prfaq', {})
        if prfaq:
            context_parts.append("\nPRFAQ:")
            if 'press_release' in prfaq:
                pr = prfaq['press_release']
                context_parts.append(f"- Press Release: {pr[:100]}..." if len(pr) > 100 else pr)
            if 'frequently_asked_questions' in prfaq:
                context_parts.append("- FAQs:")
                for qa in prfaq['frequently_asked_questions'][:2]:
                    q = qa.get('question', '')
                    a = qa.get('answer', '')
                    if len(a) > 100:
                        a = a[:100] + "..."
                    context_parts.append(f"  Q: {q}")
                    context_parts.append(f"  A: {a}")

        # Add changes information if provided
        if changes:
            context_parts.append("\nChanges:")
            for doc_type, doc_changes in changes.items():
                if doc_type == 'prd':
                    context_parts.append("- Product changes:")
                    if doc_changes.get('added'):
                        context_parts.append(f"  Added: {', '.join(doc_changes['added'])}")
                    if doc_changes.get('modified'):
                        context_parts.append(f"  Modified: {', '.join(doc_changes['modified'])}")

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
            'headline': f"Cut documentation time by 62%",
            'pain_point': "Your team wastes 4+ hours weekly reconciling inconsistent documentation across systems. This leads to implementation errors and project delays.",
            'solution': f"{project_name} monitors all connected documents for changes and automatically flags inconsistencies. It suggests specific updates to maintain alignment.",
            'benefits': "Reduce documentation busywork by 62%. Decrease implementation errors by 45%. Improve cross-team alignment with 85% fewer documentation-related questions.",
            'call_to_action': f"Start a 14-day trial with your actual documents to measure time savings.",
            'alignment_check': [
                {
                    'document_type': 'PRD',
                    'potential_issue': 'Error reduction percentage may differ between documents',
                    'recommendation': 'Verify error reduction percentage is consistent across all documents'
                }
            ]
        }

        return json.dumps(messaging)

    def _generate_change_messaging(self, content, changes):
        """Generate messaging for project changes"""
        prd = content.get('prd', {})

        # Extract project name
        project_name = prd.get('name', 'Project')

        # Identify main change type
        has_new_feature = False
        feature_name = "features"
        if changes.get('prd', {}).get('added'):
            has_new_feature = True
            feature_name = changes['prd']['added'][0].replace('_', ' ')

        # Format the messaging
        if has_new_feature:
            messaging = {
                'headline': f"New: {feature_name} saves 2+ hours weekly",
                'pain_point': "Teams waste time manually tracking document changes and suggesting updates.",
                'solution': f"The new {feature_name} feature automatically detects changes and suggests specific updates. It reduces manual reconciliation work by 75% and improves documentation accuracy by 62%.",
                'call_to_action': f"Enable {feature_name} in your project settings today.",
                'alignment_check': [
                    {
                        'document_type': 'PRD',
                        'potential_issue': 'Feature implementation details may differ',
                        'recommendation': 'Update PRD with implementation details for new feature'
                    }
                ]
            }
        else:
            messaging = {
                'headline': f"{project_name} now 3x faster",
                'pain_point': "Processing large document sets previously took too long.",
                'solution': f"We've optimized the core engine to process documents 3x faster. This update also improves accuracy by 28% and adds support for 5 new document types.",
                'call_to_action': "Update to the latest version to access these improvements.",
                'alignment_check': [
                    {
                        'document_type': 'Tickets',
                        'potential_issue': 'Performance improvement may not be reflected in tickets',
                        'recommendation': 'Update tickets to reflect new performance metrics'
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

    def _create_project_prompt(self, context):
        """Create prompt for generating messaging for the entire project"""
        # Instead of defining the prompt here, use the centralized prompt
        return get_prompt('external_messaging', context)

    def _create_changes_prompt(self, context, changes):
        """Create prompt for generating messaging about project changes"""
        # Extract project name for use in the prompt
        project_name = "Project Alignment Tool"  # Default name

        # Instead of defining the prompt here, use the centralized prompt
        return get_prompt('external_changes', context, changes=json.dumps(changes), project_name=project_name)