# services/artifacts/objection_generator.py
import json
import logging
from models import Project
from .base_generator import BaseGenerator

class ObjectionGenerator(BaseGenerator):
    """
    Service for generating critical objections to challenge user thinking.

    This service generates well-reasoned objections to project artifacts to
    encourage critical thinking and improve the quality of the final content.
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

        role = "You are a Critical Thinking Expert and Strategic Analyst with extensive experience in project evaluation, strategic planning, and identifying blind spots in business initiatives. You excel at identifying inconsistencies, challenging assumptions, and offering valuable counterpoints."

        context_text = f"""
You are evaluating a project description for a business initiative. This description will be used to communicate what the project is, what problem it's solving, and how it plans to address it.

The project context is:
{context}

The current project description is:
{json.dumps(description, indent=2)}
"""

        task = """
Your task is to generate thoughtful, substantive objections to the project description that challenge core assumptions and identify potential blind spots. These objections should help improve the description and underlying strategy by highlighting weaknesses, inconsistencies, or alternative perspectives.
"""

        format_guidelines = """
Structure your response as a JSON array of objection objects, each containing:
1. A "title" field with a concise name for the objection (5-8 words)
2. An "explanation" field with a detailed explanation (50-100 words)

Example structure:
[
    {
        "title": "Title of first objection",
        "explanation": "Detailed explanation of why this is a concern"
    },
    ...
]
"""

        process = """
Follow these steps to develop effective objections:
1. Analyze the project description for underlying assumptions
2. Identify potential inconsistencies or gaps in logic
3. Consider alternative perspectives or approaches
4. Evaluate whether the problem statement is properly defined
5. Assess if the solution directly addresses the stated problem
6. Generate 3-5 substantive objections that would improve the project if addressed
"""

        content_req = """
Your objections must:
- Be substantive and specific to this project (not generic)
- Challenge core assumptions rather than superficial details
- Identify potential blind spots in thinking
- Suggest alternative perspectives not considered
- Focus on strategic issues, not just tactical or implementation concerns
- Be constructive in nature, even while being critical
"""

        constraints = """
Avoid:
- Objections that are purely stylistic or formatting-based
- Critiques that don't offer a clear alternative perspective
- Generic objections that could apply to any project
- Focusing only on minor details rather than strategic issues
- Being unnecessarily harsh or negative in tone
"""

        examples = """
Example high-quality objections:

[
    {
        "title": "Undefined Success Metrics",
        "explanation": "The description claims significant improvements but doesn't define specific, measurable success criteria. Without clear metrics, it will be difficult to evaluate if the project achieves its goals or justify continued investment."
    },
    {
        "title": "Alternative Solutions Not Considered",
        "explanation": "The description presents a single solution approach without acknowledging alternatives. This suggests insufficient exploration of options and risks overcommitting to one path without evaluating potential simpler or more cost-effective approaches."
    }
]
"""

        interaction = """
These objections will be presented to the user alongside the project description to encourage critical thinking. They should be thought-provoking but presented in a professional, constructive manner.
"""

        quality = """
Before finalizing your objections, verify that each one:
- Identifies a specific, substantive issue in the project description
- Provides clear reasoning for why this is a problem
- Offers perspective that would genuinely improve the project if addressed
- Uses clear, professional language
- Varies in focus (don't have all objections target the same aspect)
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

        role = "You are a Strategic Communications Analyst and Internal Stakeholder Advocate with expertise in organizational communication, change management, and identifying potential misalignments between messaging and business realities."

        context_text = f"""
You are evaluating internal messaging for a business initiative. This messaging will be used to communicate with team members and stakeholders within the organization.

The project context is:
{context}

The current internal messaging is:
{json.dumps(messaging, indent=2)}
"""

        task = """
Your task is to generate thoughtful objections to the internal messaging that challenge assumptions, identify potential communication issues, and highlight areas where the messaging may not fully address stakeholder concerns or business realities.
"""

        format_guidelines = """
Structure your response as a JSON array of objection objects, each containing:
1. A "title" field with a concise name for the objection (5-8 words)
2. An "explanation" field with a detailed explanation (50-100 words)

Example structure:
[
    {
        "title": "Title of first objection",
        "explanation": "Detailed explanation of why this is a concern"
    },
    ...
]
"""

        process = """
Follow these steps to develop effective objections:
1. Analyze the internal messaging for clarity and completeness
2. Identify potential stakeholder questions or concerns not addressed
3. Consider how different internal audiences might interpret the messaging
4. Evaluate whether business impact is realistically presented
5. Assess if the messaging creates alignment with organizational priorities
6. Generate 3-5 substantive objections that would improve the messaging if addressed
"""

        content_req = """
Your objections must:
- Highlight potential disconnects between messaging and business realities
- Identify stakeholder perspectives that might be overlooked
- Address potential implementation or resource concerns
- Consider organizational culture and change management implications
- Challenge overly optimistic claims or timelines
- Suggest areas where more specific information would be beneficial
"""

        constraints = """
Avoid:
- Objections that focus solely on wording or style 
- Generic critiques that could apply to any internal communication
- Focusing on minor details rather than substantive communication issues
- Suggesting complete rewrites rather than targeted improvements
- Being unnecessarily negative or undermining the project's goals
"""

        examples = """
Example high-quality objections:

[
    {
        "title": "Resource Requirements Not Addressed",
        "explanation": "The messaging presents benefits without acknowledging the resources needed from teams. This creates risk of resistance when implementation requires unplanned effort from already-busy departments. Adding specific resource needs would set realistic expectations."
    },
    {
        "title": "Oversimplified Business Impact",
        "explanation": "The business impact is presented as universally positive without acknowledging potential tradeoffs or temporary disruptions. This may reduce credibility with experienced stakeholders who expect a more nuanced discussion of both benefits and challenges."
    }
]
"""

        interaction = """
These objections will be presented alongside the internal messaging to encourage critical thinking and improve communication planning. They should be thoughtful and constructive, helping the user strengthen their internal communications.
"""

        quality = """
Before finalizing your objections, verify that each one:
- Addresses a substantive concern about the effectiveness of the internal messaging
- Provides clear reasoning that would resonate with experienced business stakeholders
- Offers perspective that would genuinely improve internal alignment if addressed
- Uses professional language appropriate for business communications
- Focuses on different aspects of the messaging (audience considerations, business impact, resource implications, etc.)
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

        role = "You are a Customer Advocacy Specialist and Marketing Communications Expert with extensive experience in product messaging, customer psychology, and identifying disconnects between marketing claims and customer realities."

        context_text = f"""
You are evaluating external messaging for a product or service. This messaging will be used to communicate with customers and potential users outside the organization.

The project context is:
{context}

The current external messaging is:
{json.dumps(messaging, indent=2)}
"""

        task = """
Your task is to generate thoughtful objections to the external messaging that challenge assumptions, identify potential customer concerns or objections, and highlight areas where the messaging may not fully resonate with the target audience.
"""

        format_guidelines = """
Structure your response as a JSON array of objection objects, each containing:
1. A "title" field with a concise name for the objection (5-8 words)
2. An "explanation" field with a detailed explanation (50-100 words)

Example structure:
[
    {
        "title": "Title of first objection",
        "explanation": "Detailed explanation of why this is a concern"
    },
    ...
]
"""

        process = """
Follow these steps to develop effective objections:
1. Analyze the external messaging from a customer's perspective
2. Identify potential skepticism, concerns, or objections customers might have
3. Consider how different segments of the target audience might respond
4. Evaluate whether the value proposition is clearly and convincingly presented
5. Assess if the messaging addresses potential barriers to adoption
6. Generate 3-5 substantive objections that would improve the messaging if addressed
"""

        content_req = """
Your objections must:
- Highlight potential disconnects between messaging and customer expectations
- Identify customer concerns that might be unaddressed
- Address competitive or alternative solution considerations
- Consider the clarity and credibility of claims from a customer perspective
- Challenge assumptions about customer pain points or priorities
- Suggest areas where messaging could be more convincing or relevant
"""

        constraints = """
Avoid:
- Objections that focus solely on wording or style 
- Generic marketing critiques that could apply to any product
- Focusing on internal business concerns rather than customer perspective
- Suggesting complete rewrites rather than targeted improvements
- Advocating for misleading or exaggerated claims
"""

        examples = """
Example high-quality objections:

[
    {
        "title": "Value Proposition Lacks Specificity",
        "explanation": "The messaging makes general claims about benefits without specific, tangible outcomes customers can expect. Without concrete examples or metrics, potential customers may struggle to understand exactly how this solution will improve their situation compared to alternatives."
    },
    {
        "title": "Adoption Barriers Not Addressed",
        "explanation": "While the messaging highlights benefits, it doesn't address common concerns about implementation effort, learning curve, or integration with existing systems. This leaves potential objections unaddressed and may reduce conversion rates for prospects who are concerned about these practical aspects."
    }
]
"""

        interaction = """
These objections will be presented alongside the external messaging to encourage critical thinking and improve customer communication. They should be thoughtful and constructive, helping the user strengthen their value proposition and persuasiveness.
"""

        quality = """
Before finalizing your objections, verify that each one:
- Represents a credible customer perspective or concern
- Identifies a specific issue that could impact messaging effectiveness
- Provides clear reasoning that would improve customer conversion if addressed
- Uses clear language focused on customer impact
- Focuses on different aspects of the messaging (value proposition, differentiation, credibility, etc.)
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

        context = []

        # Add PRD information
        prd = content.get('prd', {})
        if prd:
            context.append("== Product Requirements Document (PRD) ==")
            for key, value in prd.items():
                if isinstance(value, str) and value:
                    context.append(f"{key.replace('_', ' ').title()}: {value}")

        # Add PRFAQ information
        prfaq = content.get('prfaq', {})
        if prfaq:
            context.append("\n== Press Release / FAQ ==")
            if 'press_release' in prfaq:
                context.append(f"Press Release: {prfaq['press_release']}")
            if 'frequently_asked_questions' in prfaq:
                context.append("FAQs:")
                for qa in prfaq['frequently_asked_questions']:
                    context.append(f"Q: {qa.get('question', '')}")
                    context.append(f"A: {qa.get('answer', '')}")

        # Add strategy information
        strategy = content.get('strategy', {})
        if strategy:
            context.append("\n== Strategy Document ==")
            for key, value in strategy.items():
                if isinstance(value, str) and value:
                    context.append(f"{key.replace('_', ' ').title()}: {value}")

        # Add ticket information (summarized)
        tickets = content.get('tickets', [])
        if tickets:
            context.append("\n== Tickets Summary ==")
            context.append(f"Total tickets: {len(tickets)}")
            for i, ticket in enumerate(tickets[:5]):  # Limit to first 5 tickets
                context.append(f"Ticket {i+1}: {ticket.get('title', '')} - {ticket.get('status', '')}")
            if len(tickets) > 5:
                context.append(f"... and {len(tickets) - 5} more tickets")

        return "\n".join(context)

    def _fallback_description_objections(self, description):
        """Provide fallback objections for project description if Claude fails."""
        return json.dumps([
            {
                "title": "Value Proposition Lacks Specificity",
                "explanation": "The messaging makes generic claims about benefits without providing specific, tangible outcomes customers can expect. Without concrete examples or metrics, potential customers may dismiss these as marketing hype."
            },
            {
                "title": "Competitive Differentiation Missing",
                "explanation": "The messaging doesn't clearly explain how this solution differs from alternatives already available to customers. Without clear differentiation, customers have no compelling reason to switch from their current solutions."
            },
            {
                "title": "Customer Objections Not Addressed",
                "explanation": "The messaging focuses only on benefits but doesn't address common concerns or objections customers might have about implementation, compatibility, or learning curve. This leaves potential obstacles to conversion unaddressed."
            }
        ])
                "title": "Unclear Problem Definition",
                "explanation": "The description doesn't clearly quantify the problem's impact or provide evidence that it's a significant issue worth solving. Without clear metrics and examples, it's difficult to evaluate the project's potential value."
            },
            {
                "title": "Alternative Solutions Not Addressed",
                "explanation": "The description doesn't explain why this particular solution approach was chosen over alternatives. This creates the risk that simpler or more effective solutions may have been overlooked."
            },
            {
                "title": "Implementation Challenges Understated",
                "explanation": "The description minimizes potential implementation challenges, particularly around integration with existing systems and processes. This could lead to unrealistic expectations and execution issues."
            }
        ])

    def _fallback_internal_objections(self, messaging):
        """Provide fallback objections for internal messaging if Claude fails."""
        return json.dumps([
            {
                "title": "Resource Requirements Not Addressed",
                "explanation": "The messaging doesn't clearly outline the resources and time commitment required from teams. This could lead to resistance when implementation requires unexpected effort from already-busy departments."
            },
            {
                "title": "Success Metrics Missing",
                "explanation": "The messaging doesn't define specific success metrics or KPIs. Without clear measurements, teams may not understand what they're working toward or how success will be evaluated."
            },
            {
                "title": "Change Management Needs Overlooked",
                "explanation": "The messaging focuses on the solution but overlooks the organizational change management aspects. New tools and processes often face adoption challenges that should be proactively addressed."
            }
        ])

    def _fallback_external_objections(self, messaging):
        """Provide fallback objections for external messaging if Claude fails."""
        return json.dumps([
            {