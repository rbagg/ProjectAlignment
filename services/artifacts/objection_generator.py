# services/artifacts/objection_generator.py
import json
import logging
from models import Project
from .base_generator import BaseGenerator
from prompts import get_prompt

class ObjectionGenerator(BaseGenerator):
    """
    Generates critical objections to project artifacts.
    Core feature for challenging assumptions and improving communication.
    """

    def get_latest(self):
        """
        Get latest objections from database.
        Required implementation of abstract method from BaseGenerator.

        Returns:
            dict: Latest objections or None
        """
        project = Project.query.order_by(Project.timestamp.desc()).first()
        if not project:
            return None

        return {
            'description': project.get_description_objections_list(),
            'internal': project.get_internal_objections_list(),
            'external': project.get_external_objections_list()
        }

    def generate(self, project_content, artifact_type='description'):
        """
        Generate objections for project content.
        Required implementation of abstract method from BaseGenerator.

        Args:
            project_content (str): JSON string of project content
            artifact_type (str): Type of artifact to generate objections for

        Returns:
            str: JSON string of objections
        """
        content = self.parse_content(project_content)

        # For this method, we'll just use generate_for_artifact
        # with a dummy artifact content since that's what we actually want to use
        dummy_artifact = {"type": artifact_type}
        return self.generate_for_artifact(content, dummy_artifact, artifact_type)

    def generate_for_artifact(self, project_content, artifact_content, artifact_type):
        """
        Generate objections for a specific artifact.

        Args:
            project_content (dict): The project content
            artifact_content (dict): The artifact content to critique
            artifact_type (str): Type of artifact ('description', 'internal', 'external')

        Returns:
            str: JSON string of objections
        """
        # Format context for the objection prompt
        context = self._format_context(project_content)

        # Convert artifact content to a formatted string
        artifact_string = json.dumps(artifact_content, indent=2)

        # Get objection generator prompt from centralized prompt system
        prompt = get_prompt('objection_generator', context, artifact=artifact_string, artifact_type=artifact_type)

        # Generate objections
        objections_json = self.generate_with_claude(
            prompt=prompt,
            fallback_method=self._fallback_objections,
            fallback_args={'artifact_type': artifact_type}
        )

        return objections_json

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

    def _fallback_objections(self, artifact_type):
        """Provide fallback objections if Claude fails."""
        if artifact_type == 'description':
            return json.dumps([
                {
                    "title": "No Success Metrics",
                    "explanation": "The description lacks measurable KPIs to evaluate success.",
                    "impact": "Projects without metrics show 40% higher failure rates."
                },
                {
                    "title": "Alternatives Not Compared",
                    "explanation": "No explanation of why this approach beats alternatives.",
                    "impact": "Insufficient alternative analysis increases project pivots by 35%."
                },
                {
                    "title": "Integration Requirements Missing",
                    "explanation": "No mention of how this integrates with existing systems.",
                    "impact": "Integration planning gaps cause 50% of implementation delays."
                }
            ])
        elif artifact_type == 'internal':
            return json.dumps([
                {
                    "title": "Resource Requirements Unspecified",
                    "explanation": "Message doesn't detail team resources needed.",
                    "impact": "Resource planning gaps cause 30% of project delays."
                },
                {
                    "title": "No Timeline Provided",
                    "explanation": "No mention of key milestones or deadlines.",
                    "impact": "Timeline omissions lead to 35% of projects missing deadlines."
                },
                {
                    "title": "Success Metrics Undefined",
                    "explanation": "No specific KPIs for measuring project success.",
                    "impact": "Undefined metrics lead to 25% increase in scope creep."
                }
            ])
        elif artifact_type == 'external':
            return json.dumps([
                {
                    "title": "Value Not Quantified",
                    "explanation": "Mentions benefits without quantifying customer impact.",
                    "impact": "Non-quantified value props convert 35% worse than specific ones."
                },
                {
                    "title": "No Differentiation",
                    "explanation": "Doesn't explain advantages over competitor solutions.",
                    "impact": "Undifferentiated messaging reduces conversion by 28%."
                },
                {
                    "title": "Implementation Effort Unstated",
                    "explanation": "Doesn't address customer effort to implement.",
                    "impact": "Unstated implementation requirements increase sales cycle by 40%."
                }
            ])
        else:
            return json.dumps([
                {
                    "title": "Insufficient Detail",
                    "explanation": "The artifact lacks necessary detail for evaluation.",
                    "impact": "Insufficient detail leads to 40% more implementation questions."
                }
            ])

    def _generate_description_objections(self, project_content, description):
        """Generate objections to the project description."""
        context = self._format_context(project_content)

        # Convert artifact content to a formatted string
        artifact_string = json.dumps(description, indent=2)

        # Get objection generator prompt from centralized prompt system
        prompt = get_prompt('objection_generator', context, artifact=artifact_string, artifact_type='description')

        return self.generate_with_claude(
            prompt=prompt,
            fallback_method=self._fallback_objections,
            fallback_args={'artifact_type': 'description'}
        )

    def _generate_internal_objections(self, project_content, messaging):
        """Generate objections to the internal messaging."""
        context = self._format_context(project_content)

        # Convert artifact content to a formatted string
        artifact_string = json.dumps(messaging, indent=2)

        # Get objection generator prompt from centralized prompt system
        prompt = get_prompt('objection_generator', context, artifact=artifact_string, artifact_type='internal')

        return self.generate_with_claude(
            prompt=prompt,
            fallback_method=self._fallback_objections,
            fallback_args={'artifact_type': 'internal'}
        )

    def _generate_external_objections(self, project_content, messaging):
        """Generate objections to the external messaging."""
        context = self._format_context(project_content)

        # Convert artifact content to a formatted string
        artifact_string = json.dumps(messaging, indent=2)

        # Get objection generator prompt from centralized prompt system
        prompt = get_prompt('objection_generator', context, artifact=artifact_string, artifact_type='external')

        return self.generate_with_claude(
            prompt=prompt,
            fallback_method=self._fallback_objections,
            fallback_args={'artifact_type': 'external'}
        )