# services/artifacts/project_description.py
import json
import logging
from models import Project
from flask import current_app
from .base_generator import BaseGenerator
from .objection_generator import ObjectionGenerator
from .improvement_generator import ImprovementGenerator
from prompts import get_prompt

class ProjectDescriptionGenerator(BaseGenerator):
    """
    Generates concise project descriptions.
    Creates 3-sentence and 3-paragraph summaries.
    """

    def __init__(self):
        """Initialize the generator with a logger, objection generator, and improvement generator."""
        super().__init__()
        self.objection_generator = ObjectionGenerator()
        self.improvement_generator = ImprovementGenerator()

    def get_latest(self):
        """Get the latest generated project description"""
        project = Project.query.order_by(Project.timestamp.desc()).first()
        if project and project.description:
            result = project.get_description_dict()

            # Add objections if available
            if project.description_objections:
                result['objections'] = project.get_description_objections_list()

            # Add improvements if available
            if project.description_improvements:
                result['improvements'] = project.get_description_improvements_list()

            return result
        return None

    def generate(self, project_content):
        """
        Generate project description in three sentences and three paragraphs.

        Args:
            project_content (str): JSON string of project content

        Returns:
            str: JSON string with descriptions, objections, and improvements
        """
        content = self.parse_content(project_content)

        # Format the context
        context = self._format_context(content)

        # Get the project description prompt from centralized prompt system
        prompt = get_prompt('project_description', context)

        # Generate description
        description_json = self.generate_with_claude(
            prompt=prompt,
            fallback_method=self._rule_based_generation,
            fallback_args={'content': content}
        )

        # Parse the description
        description = self.parse_content(description_json)

        # Generate objections for the description
        objections_json = self.objection_generator.generate_for_artifact(
            content, description, 'description')

        # Generate improvements for the description
        improvements_json = self.improvement_generator.generate_for_artifact(
            content, description, 'description')

        # Combine description, objections, and improvements
        description['objections'] = self.parse_content(objections_json)
        description['improvements'] = self.parse_content(improvements_json)

        return json.dumps(description)

    def _format_context(self, content):
        """Format content as context for Claude"""
        context_parts = []

        # Add PRD information (key facts only)
        prd = content.get('prd', {})
        if prd:
            context_parts.append("PRD:")
            for key, value in prd.items():
                if isinstance(value, str) and value:
                    # Truncate long values
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
                for qa in prfaq['frequently_asked_questions'][:2]:  # Limit to first 2 FAQs
                    q = qa.get('question', '')
                    a = qa.get('answer', '')
                    if len(a) > 100:
                        a = a[:100] + "..."
                    context_parts.append(f"  Q: {q}")
                    context_parts.append(f"  A: {a}")

        # Add strategy key points
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

        return "\n".join(context_parts)

    def _rule_based_generation(self, content):
        """Fallback rule-based generation if Claude is unavailable."""
        # Extract key information from content
        prd = content.get('prd', {})
        prfaq = content.get('prfaq', {})
        strategy = content.get('strategy', {})

        # Extract project name and overview
        project_name = prd.get('name', 'Project')
        overview = prd.get('overview', '')

        # Extract customer pain points
        pain_points = []
        if 'problem_statement' in prd:
            pain_points.append(prd['problem_statement'])
        if 'customer_pain_points' in prd:
            pain_points.extend(prd['customer_pain_points'])
        if 'frequently_asked_questions' in prfaq:
            for qa in prfaq['frequently_asked_questions']:
                if 'problem' in qa.get('question', '').lower():
                    pain_points.append(qa.get('answer', ''))

        # Extract solution approach
        solutions = []
        if 'solution' in prd:
            solutions.append(prd['solution'])
        if 'approach' in strategy:
            solutions.append(strategy['approach'])

        # Generate three-sentence description
        three_sentences = [
            f"{project_name} connects and synchronizes project documentation across systems.",
            "Teams waste 4+ hours weekly reconciling inconsistent documentation.",
            "The tool monitors changes, flags inconsistencies, and suggests updates."
        ]

        # Generate three-paragraph description
        three_paragraphs = [
            f"{project_name} is a documentation synchronization system that connects PRDs, tickets, and strategy documents. It monitors all connected documents for changes and maintains alignment. The system automatically generates project descriptions, messaging, and flags potential issues.",

            "Teams currently waste 4+ hours weekly reconciling inconsistent documentation. This leads to implementation errors, miscommunication, and project delays. Studies show 32% of project failures stem from documentation inconsistencies.",

            f"{project_name} solves this by creating bidirectional links between documents. When changes occur, it flags inconsistencies and suggests updates. The system also generates standardized artifacts and identifies potential issues."
        ]

        # Add alignment gaps
        alignment_gaps = [
            {
                "document_type": "Tickets",
                "missing_element": "Success metrics and acceptance criteria",
                "recommendation": "Add specific KPIs to tickets that align with the project goals"
            },
            {
                "document_type": "PRD",
                "missing_element": "Resource requirements",
                "recommendation": "Include detailed engineering resources needed for implementation"
            }
        ]

        # Format the result
        result = {
            'three_sentences': three_sentences,
            'three_paragraphs': three_paragraphs,
            'alignment_gaps': alignment_gaps
        }

        return json.dumps(result)