# services/artifacts/objection_generator.py
import json
import logging
from models import Project
from .base_generator import BaseGenerator

class ObjectionGenerator(BaseGenerator):
    """
    Generates critical objections to project artifacts.
    Core feature for challenging assumptions and improving communication.
    """

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
        # Format the objection prompt based on artifact type
        if artifact_type == 'description':
            return self._generate_description_objections(project_content, artifact_content)
        elif artifact_type == 'internal':
            return self._generate_internal_objections(project_content, artifact_content)
        elif artifact_type == 'external':
            return self._generate_external_objections(project_content, artifact_content)
        else:
            self.logger.error(f"Unknown artifact type: {artifact_type}")
            return json.dumps([])

    def _generate_description_objections(self, project_content, description):
        """Generate objections to the project description."""
        context = self._format_context(project_content)

        role = "You are a Critical Project Evaluator who identifies flaws in project descriptions."

        context_text = f"""
Project description to evaluate:
{json.dumps(description, indent=2)}

Project context:
{context}
"""

        task = """
Generate 3-5 factual, concrete objections to this project description. Focus on obvious flaws that would prevent project success.
"""

        format_guidelines = """
Format as a JSON array of objection objects with:
1. "title" - 3-6 word summary of the issue
2. "explanation" - 1-2 sentence factual explanation
3. "impact" - quantifiable business impact (when possible)

Example format:
[
    {
        "title": "No Success Metrics",
        "explanation": "The description lacks measurable KPIs to evaluate success.",
        "impact": "Projects without metrics show 40% higher failure rates."
    }
]
"""

        process = """
1. Identify missing critical information
2. Spot logical inconsistencies
3. Note unrealistic assumptions
4. Find areas lacking specificity
5. Focus on objections with highest business impact
"""

        content_req = """
Objections must be:
- Factual rather than opinion-based
- Specific to this project (not generic)
- Concise and direct (no marketing language)
- Quantifiable when possible
- Focused on critical flaws first
"""

        constraints = """
Avoid:
- Stylistic or formatting critiques
- Minor issues with minimal impact
- Subjective opinions about approach
- Lengthy explanations
- Flowery or overly polite language
"""

        examples = """
Example objections:

[
    {
        "title": "No Success Metrics",
        "explanation": "The description lacks measurable KPIs to evaluate success.",
        "impact": "Projects without metrics show 40% higher failure rates."
    },
    {
        "title": "Resources Unspecified",
        "explanation": "Required team size and budget aren't defined.",
        "impact": "Resource planning gaps cause 30% of project delays."
    },
    {
        "title": "Stakeholders Not Identified",
        "explanation": "Key project stakeholders and their needs aren't listed.",
        "impact": "Stakeholder omissions cause 45% of scope creep issues."
    }
]
"""

        interaction = """
These objections will challenge the project team to address critical issues before proceeding.
"""

        quality = """
Verify each objection:
- Addresses a genuine business risk
- Identifies a specific, actionable issue
- Is factual and evidence-based
- Avoids subjective language
- Includes likely business impact
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
            fallback_method=self._fallback_description_objections,
            fallback_args={'description': description}
        )

    def _generate_internal_objections(self, project_content, messaging):
        """Generate objections to the internal messaging."""
        context = self._format_context(project_content)

        role = "You are a Critical Communications Analyst who identifies flaws in internal project messaging."

        context_text = f"""
Internal messaging to evaluate:
{json.dumps(messaging, indent=2)}

Project context:
{context}
"""

        task = """
Generate 3-5 factual, direct objections to this internal messaging. Focus on communication gaps that would cause team confusion or project misalignment.
"""

        format_guidelines = """
Format as a JSON array of objection objects with:
1. "title" - 3-6 word summary of the issue
2. "explanation" - 1-2 sentence factual explanation 
3. "impact" - quantifiable business impact (when possible)

Example format:
[
    {
        "title": "Timeline Not Addressed",
        "explanation": "Message lacks project timeline and key milestones.",
        "impact": "Timeline omissions cause 35% of deadline failures."
    }
]
"""

        process = """
1. Identify missing operational details
2. Spot team coordination gaps
3. Note unstated dependencies
4. Find resource requirement omissions
5. Focus on objections with highest team impact
"""

        content_req = """
Objections must be:
- Factual rather than opinion-based
- Specific to this internal message
- Concise and direct
- Focused on operational issues
- Quantifiable when possible
"""

        constraints = """
Avoid:
- Style or tone critiques
- Minor wording issues
- Subjective opinions
- Lengthy explanations
- Flowery or overly polite language
"""

        examples = """
Example objections:

[
    {
        "title": "Team Roles Undefined",
        "explanation": "Message doesn't clarify which teams own which deliverables.",
        "impact": "Role ambiguity causes 25% of internal project conflicts."
    },
    {
        "title": "Dependencies Not Listed",
        "explanation": "Critical cross-team dependencies aren't mentioned.",
        "impact": "Unidentified dependencies cause 40% of project delays."
    },
    {
        "title": "Prioritization Missing",
        "explanation": "No guidance on feature priority if resources constrained.",
        "impact": "Priority gaps lead to 30% wasted development effort."
    }
]
"""

        interaction = """
These objections will help improve internal alignment and prevent common team coordination issues.
"""

        quality = """
Verify each objection:
- Addresses a genuine operational risk
- Identifies a specific, actionable issue
- Is factual and evidence-based
- Avoids subjective language
- Includes likely business impact
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
            fallback_method=self._fallback_internal_objections,
            fallback_args={'messaging': messaging}
        )

    def _generate_external_objections(self, project_content, messaging):
        """Generate objections to the external messaging."""
        context = self._format_context(project_content)

        role = "You are a Customer Perspective Analyst who identifies flaws in product messaging."

        context_text = f"""
External messaging to evaluate:
{json.dumps(messaging, indent=2)}

Project context:
{context}
"""

        task = """
Generate 3-5 factual, direct objections to this external messaging. Focus on issues that would reduce customer conversion or create misaligned expectations.
"""

        format_guidelines = """
Format as a JSON array of objection objects with:
1. "title" - 3-6 word summary of the issue
2. "explanation" - 1-2 sentence factual explanation
3. "impact" - quantifiable business impact (when possible)

Example format:
[
    {
        "title": "Value Not Quantified",
        "explanation": "Messaging states benefits but doesn't quantify customer impact.",
        "impact": "Non-quantified value propositions convert 35% worse than specific ones."
    }
]
"""

        process = """
1. Identify vague benefit claims
2. Spot missing proof points
3. Note unaddressed customer concerns
4. Find competitive differentiation gaps
5. Focus on objections with highest conversion impact
"""

        content_req = """
Objections must be:
- Factual rather than opinion-based
- Specific to this customer message
- Concise and direct
- Focused on conversion obstacles
- Quantifiable when possible
"""

        constraints = """
Avoid:
- Style or tone critiques
- Minor wording issues
- Subjective opinions
- Lengthy explanations
- Flowery language
"""

        examples = """
Example objections:

[
    {
        "title": "No Social Proof",
        "explanation": "Message contains no customer examples or testimonials.",
        "impact": "Messaging without social proof converts 42% worse."
    },
    {
        "title": "Implementation Effort Unstated",
        "explanation": "Doesn't address how much work customers must do to implement.",
        "impact": "Unstated implementation requirements increase sales cycle by 40%."
    },
    {
        "title": "Pricing Model Unclear",
        "explanation": "Doesn't indicate if pricing is subscription, one-time, or usage-based.",
        "impact": "Pricing ambiguity decreases landing page conversion by 28%."
    }
]
"""

        interaction = """
These objections will help improve conversion rates and set appropriate customer expectations.
"""

        quality = """
Verify each objection:
- Addresses a genuine conversion obstacle
- Identifies a specific, actionable issue
- Is factual and evidence-based
- Avoids subjective language
- Includes likely business impact
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
            fallback_method=self._fallback_external_objections,
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

    def _fallback_description_objections(self, description):
        """Provide fallback objections for project description if Claude fails."""
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

    def _fallback_internal_objections(self, messaging):
        """Provide fallback objections for internal messaging if Claude fails."""
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

    def _fallback_external_objections(self, messaging):
        """Provide fallback objections for external messaging if Claude fails."""
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