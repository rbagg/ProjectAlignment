# services/artifacts/improvement_generator.py
import json
import logging
from models import Project
from .base_generator import BaseGenerator
from prompts import get_prompt

class ImprovementGenerator(BaseGenerator):
    """
    Generates positive improvement suggestions for project artifacts.
    Provides actionable ways to strengthen communication and prevent scope creep.
    """

    def get_latest(self):
        """
        Get latest improvements from database.
        Required implementation of abstract method from BaseGenerator.

        Returns:
            dict: Latest improvements or None
        """
        project = Project.query.order_by(Project.timestamp.desc()).first()
        if not project:
            return None

        return {
            'description': project.get_description_improvements_list(),
            'internal': project.get_internal_improvements_list(),
            'external': project.get_external_improvements_list()
        }

    def generate(self, project_content, artifact_type='description'):
        """
        Generate improvements for project content.
        Required implementation of abstract method from BaseGenerator.

        Args:
            project_content (str): JSON string of project content
            artifact_type (str): Type of artifact to generate improvements for

        Returns:
            str: JSON string of improvements
        """
        content = self.parse_content(project_content)

        # For this method, we'll just use generate_for_artifact
        # with a dummy artifact content since that's what we actually want to use
        dummy_artifact = {"type": artifact_type}
        return self.generate_for_artifact(content, dummy_artifact, artifact_type)

    def generate_for_artifact(self, project_content, artifact_content, artifact_type):
        """
        Generate improvement suggestions for a specific artifact.

        Args:
            project_content (dict): The project content
            artifact_content (dict): The artifact content to improve
            artifact_type (str): Type of artifact ('description', 'internal', 'external')

        Returns:
            str: JSON string of improvement suggestions
        """
        # Format context for the improvement prompt
        context = self._format_context(project_content)

        # Convert artifact content to a formatted string
        artifact_string = json.dumps(artifact_content, indent=2)

        # Get improvement generator prompt from centralized prompt system
        prompt = get_prompt('improvement_generator', context, artifact=artifact_string, artifact_type=artifact_type)

        # Generate improvements
        improvements_json = self.generate_with_claude(
            prompt=prompt,
            fallback_method=self._fallback_improvements,
            fallback_args={'artifact_type': artifact_type}
        )

        return improvements_json

    def _format_context(self, content):
        """Format content as context for Claude"""
        if isinstance(content, str):
            content = self.parse_content(content)

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
                context_parts.append(f"- FAQs: {len(prfaq['frequently_asked_questions'])} questions")

        # Add strategy key points
        strategy = content.get('strategy', {})
        if strategy:
            context_parts.append("\nStrategy:")
            for key, value in strategy.items():
                if isinstance(value, str) and value:
                    if len(value) > 100:
                        value = value[:100] + "..."
                    context_parts.append(f"- {key}: {value}")

        # Add ticket count only
        tickets = content.get('tickets', [])
        if tickets:
            context_parts.append(f"\nTickets: {len(tickets)} total")

        return "\n".join(context_parts)

    def _fallback_improvements(self, artifact_type):
        """Provide fallback improvements if Claude fails."""
        if artifact_type == 'description':
            return json.dumps([
                {
                    "title": "Add Success Metrics",
                    "suggestion": "Define 3-5 specific KPIs that will measure project success (e.g., 40% reduction in document sync time).",
                    "benefit": "Projects with defined metrics are 35% more likely to deliver expected business value."
                },
                {
                    "title": "Sharpen Scope Boundaries",
                    "suggestion": "Explicitly list what's NOT included in the project to prevent scope creep (e.g., 'Will not include SharePoint integration').",
                    "benefit": "Clear scope boundaries reduce feature creep by 42% and prevent 30% of project delays."
                },
                {
                    "title": "Specify Implementation Phases",
                    "suggestion": "Break implementation into 3 concrete phases with specific deliverables for each milestone.",
                    "benefit": "Phased implementation approaches reduce project risk by 38% and improve stakeholder alignment."
                }
            ])
        elif artifact_type == 'internal':
            return json.dumps([
                {
                    "title": "Add RACI Matrix",
                    "suggestion": "Include a simple RACI chart showing team responsibilities for key deliverables.",
                    "benefit": "Clear responsibility assignment reduces delivery delays by 28% and eliminates redundant work."
                },
                {
                    "title": "Prioritize Implementation Tasks",
                    "suggestion": "Categorize implementation tasks as P0 (critical), P1 (important), and P2 (nice-to-have).",
                    "benefit": "Prioritized task lists improve team focus by 32% and increase on-time delivery rates."
                },
                {
                    "title": "Add Dependency Timeline",
                    "suggestion": "Create a visual timeline showing cross-team dependencies and delivery dates.",
                    "benefit": "Dependency timelines reduce blocking issues by 45% and improve cross-team coordination."
                }
            ])
        elif artifact_type == 'external':
            return json.dumps([
                {
                    "title": "Add Customer Testimonial",
                    "suggestion": "Include a brief quote from a beta customer with specific results achieved.",
                    "benefit": "Customer testimonials increase conversion rates by 34% and build credibility."
                },
                {
                    "title": "Create Comparison Table",
                    "suggestion": "Add a simple 3-column table comparing your solution vs. alternatives vs. doing nothing.",
                    "benefit": "Direct comparison tables improve conversion by 28% by addressing alternative evaluation directly."
                },
                {
                    "title": "Add ROI Calculator Link",
                    "suggestion": "Include a link to a simple calculator where prospects can estimate their specific ROI.",
                    "benefit": "Interactive ROI tools increase qualified leads by 40% and decrease sales cycle length."
                }
            ])
        else:
            return json.dumps([
                {
                    "title": "Add Specific Examples",
                    "suggestion": "Include 2-3 concrete examples that illustrate key points.",
                    "benefit": "Specific examples improve comprehension by 42% and increase message retention."
                }
            ])

    def _generate_description_improvements(self, project_content, description):
        """Generate improvements for the project description."""
        context = self._format_context(project_content)

        # Convert artifact content to a formatted string
        artifact_string = json.dumps(description, indent=2)

        # Get improvement generator prompt from centralized prompt system
        prompt = get_prompt('improvement_generator', context, artifact=artifact_string, artifact_type='description')

        return self.generate_with_claude(
            prompt=prompt,
            fallback_method=self._fallback_improvements,
            fallback_args={'artifact_type': 'description'}
        )

    def _generate_internal_improvements(self, project_content, messaging):
        """Generate improvements for the internal messaging."""
        context = self._format_context(project_content)

        # Convert artifact content to a formatted string
        artifact_string = json.dumps(messaging, indent=2)

        # Get improvement generator prompt from centralized prompt system
        prompt = get_prompt('improvement_generator', context, artifact=artifact_string, artifact_type='internal')

        return self.generate_with_claude(
            prompt=prompt,
            fallback_method=self._fallback_improvements,
            fallback_args={'artifact_type': 'internal'}
        )

    def _generate_external_improvements(self, project_content, messaging):
        """Generate improvements for the external messaging."""
        context = self._format_context(project_content)

        # Convert artifact content to a formatted string
        artifact_string = json.dumps(messaging, indent=2)

        # Get improvement generator prompt from centralized prompt system
        prompt = get_prompt('improvement_generator', context, artifact=artifact_string, artifact_type='external')

        return self.generate_with_claude(
            prompt=prompt,
            fallback_method=self._fallback_improvements,
            fallback_args={'artifact_type': 'external'}
        )