# services/artifacts/improvement_generator.py
import json
import logging
from models import Project
from .base_generator import BaseGenerator

class ImprovementGenerator(BaseGenerator):
    """
    Generates positive improvement suggestions for project artifacts.
    Provides actionable ways to strengthen communication and prevent scope creep.
    """

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
        # Format the improvement prompt based on artifact type
        if artifact_type == 'description':
            return self._generate_description_improvements(project_content, artifact_content)
        elif artifact_type == 'internal':
            return self._generate_internal_improvements(project_content, artifact_content)
        elif artifact_type == 'external':
            return self._generate_external_improvements(project_content, artifact_content)
        else:
            self.logger.error(f"Unknown artifact type: {artifact_type}")
            return json.dumps([])

    def _generate_description_improvements(self, project_content, description):
        """Generate improvements for the project description."""
        context = self._format_context(project_content)

        role = "You are a Product Focus Specialist who helps teams sharpen project definitions and prevent scope creep."

        context_text = f"""
Project description to improve:
{json.dumps(description, indent=2)}

Project context:
{context}
"""

        task = """
Generate 3 specific, actionable improvements for this project description:
1. One suggestion to strengthen the core value proposition
2. One suggestion to prevent scope creep and maintain focus
3. One suggestion to improve clarity or specificity
"""

        format_guidelines = """
Format as a JSON array of improvement objects with:
1. "title" - 3-6 word summary of the improvement
2. "suggestion" - 1-2 sentence specific, actionable recommendation
3. "benefit" - quantifiable business outcome this will produce

Example format:
[
    {
        "title": "Strengthen Value Proposition",
        "suggestion": "Add specific ROI metrics showing 3x faster document processing.",
        "benefit": "Quantified value propositions convert 45% better than general claims."
    }
]
"""

        process = """
1. Identify the core value proposition
2. Assess scope boundaries and focus
3. Evaluate clarity and specificity
4. Develop concrete improvement suggestions
5. Ensure each suggestion is specific and actionable
6. Connect suggestions to measurable business outcomes
"""

        content_req = """
Improvements must be:
- Specific and actionable, not general advice
- Focused on strengthening the core concept, not changing it
- Practical to implement with existing information
- Connected to business outcomes
- Factual and evidence-based
- Relevant to project description content
"""

        constraints = """
Avoid:
- Vague recommendations without specifics
- Suggestions that fundamentally change the project
- Purely stylistic recommendations
- Complex improvements requiring substantial new information
- Obvious or trivial suggestions
- General best practices without specificity
"""

        examples = """
Example improvements:

[
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
]
"""

        interaction = """
These improvements will help the product manager strengthen the project definition and maintain focus on core value.
"""

        quality = """
Verify each improvement:
- Addresses a specific aspect of the project description
- Provides concrete, actionable guidance
- Connects to measurable business outcomes
- Maintains focus on core project value
- Is practical to implement with available information
"""

        prompt = self.format_prompt(
            role=role,
            context=context_text,
            task=task,
            format_guidelines=format_guidelines,
            process=process,
            content_req=content_req,
            constraints=constraints,
            examples=examples,
            interaction=interaction,
            quality=quality
        )

        return self.generate_with_claude(
            prompt=prompt,
            fallback_method=self._fallback_description_improvements,
            fallback_args={'description': description}
        )

    def _generate_internal_improvements(self, project_content, messaging):
        """Generate improvements for the internal messaging."""
        context = self._format_context(project_content)

        role = "You are an Internal Communications Specialist who helps teams strengthen project messaging for stakeholder alignment."

        context_text = f"""
Internal messaging to improve:
{json.dumps(messaging, indent=2)}

Project context:
{context}
"""

        task = """
Generate 3 specific, actionable improvements for this internal messaging:
1. One suggestion to improve cross-team alignment
2. One suggestion to clarify resource needs or dependencies
3. One suggestion to strengthen implementation focus
"""

        format_guidelines = """
Format as a JSON array of improvement objects with:
1. "title" - 3-6 word summary of the improvement
2. "suggestion" - 1-2 sentence specific, actionable recommendation
3. "benefit" - quantifiable team or business outcome this will produce

Example format:
[
    {
        "title": "Add RACI Matrix",
        "suggestion": "Include a simple RACI chart showing team responsibilities for key deliverables.",
        "benefit": "Clear responsibility assignment reduces delivery delays by 28% and eliminates redundant work."
    }
]
"""

        process = """
1. Identify cross-team alignment opportunities
2. Assess resource and dependency clarity
3. Evaluate implementation focus
4. Develop concrete improvement suggestions
5. Ensure each suggestion is specific and actionable
6. Connect suggestions to measurable team outcomes
"""

        content_req = """
Improvements must be:
- Specific and actionable, not general advice
- Focused on strengthening internal alignment
- Practical to implement immediately
- Connected to team efficiency outcomes
- Factual and evidence-based
- Relevant to the internal messaging content
"""

        constraints = """
Avoid:
- Vague recommendations without specifics
- Suggestions that require significant new research
- Purely stylistic recommendations
- Complex improvements requiring substantial rework
- Obvious or trivial suggestions
- General best practices without specificity
"""

        examples = """
Example improvements:

[
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
]
"""

        interaction = """
These improvements will help the product manager strengthen team alignment and improve implementation success.
"""

        quality = """
Verify each improvement:
- Addresses a specific aspect of the internal messaging
- Provides concrete, actionable guidance
- Connects to measurable team outcomes
- Improves cross-team alignment
- Is practical to implement immediately
"""

        prompt = self.format_prompt(
            role=role,
            context=context_text,
            task=task,
            format_guidelines=format_guidelines,
            process=process,
            content_req=content_req,
            constraints=constraints,
            examples=examples,
            interaction=interaction,
            quality=quality
        )

        return self.generate_with_claude(
            prompt=prompt,
            fallback_method=self._fallback_internal_improvements,
            fallback_args={'messaging': messaging}
        )

    def _generate_external_improvements(self, project_content, messaging):
        """Generate improvements for the external messaging."""
        context = self._format_context(project_content)

        role = "You are a Customer Value Specialist who helps teams strengthen product messaging for maximum conversion."

        context_text = f"""
External messaging to improve:
{json.dumps(messaging, indent=2)}

Project context:
{context}
"""

        task = """
Generate 3 specific, actionable improvements for this external messaging:
1. One suggestion to strengthen the value proposition
2. One suggestion to improve conversion potential
3. One suggestion to differentiate from alternatives
"""

        format_guidelines = """
Format as a JSON array of improvement objects with:
1. "title" - 3-6 word summary of the improvement
2. "suggestion" - 1-2 sentence specific, actionable recommendation
3. "benefit" - quantifiable conversion or customer outcome this will produce

Example format:
[
    {
        "title": "Add Customer Testimonial",
        "suggestion": "Include a brief quote from a beta customer with specific results achieved.",
        "benefit": "Customer testimonials increase conversion rates by 34% and build credibility."
    }
]
"""

        process = """
1. Identify value proposition opportunities
2. Assess conversion potential
3. Evaluate competitive differentiation
4. Develop concrete improvement suggestions
5. Ensure each suggestion is specific and actionable
6. Connect suggestions to measurable customer outcomes
"""

        content_req = """
Improvements must be:
- Specific and actionable, not general advice
- Focused on strengthening customer appeal
- Practical to implement immediately
- Connected to conversion outcomes
- Factual and evidence-based
- Relevant to the external messaging content
"""

        constraints = """
Avoid:
- Vague recommendations without specifics
- Suggestions that require significant new research
- Purely stylistic recommendations
- Complex improvements requiring substantial rework
- Obvious or trivial suggestions
- General marketing best practices without specificity
"""

        examples = """
Example improvements:

[
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
]
"""

        interaction = """
These improvements will help the product manager strengthen customer messaging and improve conversion rates.
"""

        quality = """
Verify each improvement:
- Addresses a specific aspect of the external messaging
- Provides concrete, actionable guidance
- Connects to measurable customer outcomes
- Strengthens competitive positioning
- Is practical to implement immediately
"""

        prompt = self.format_prompt(
            role=role,
            context=context_text,
            task=task,
            format_guidelines=format_guidelines,
            process=process,
            content_req=content_req,
            constraints=constraints,
            examples=examples,
            interaction=interaction,
            quality=quality
        )

        return self.generate_with_claude(
            prompt=prompt,
            fallback_method=self._fallback_external_improvements,
            fallback_args={'messaging': messaging}
        )

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

    def _fallback_description_improvements(self, description):
        """Provide fallback improvements for project description if Claude fails."""
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

    def _fallback_internal_improvements(self, messaging):
        """Provide fallback improvements for internal messaging if Claude fails."""
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

    def _fallback_external_improvements(self, messaging):
        """Provide fallback improvements for external messaging if Claude fails."""
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