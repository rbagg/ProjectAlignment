# services/artifacts/internal_messaging.py
import json
import logging
from models import Project
from flask import current_app
from .base_generator import BaseGenerator
from .objection_generator import ObjectionGenerator

class InternalMessagingGenerator(BaseGenerator):
    """
    Generator for internal messaging about the project.

    This service creates messaging for internal stakeholders about what
    the project is, the customer pain point it addresses, the solution
    approach, and the business impact, along with objections to challenge
    thinking.
    """

    def __init__(self):
        """Initialize the generator with a logger and objection generator."""
        super().__init__()
        self.objection_generator = ObjectionGenerator()

    def get_latest(self):
        """Get the latest generated internal messaging"""
        project = Project.query.order_by(Project.timestamp.desc()).first()
        if project and project.internal_messaging:
            result = project.get_internal_messaging_dict()

            # Add objections if available
            if project.internal_objections:
                result['objections'] = project.get_internal_objections_list()

            return result
        return None

    def generate(self, project_content, changes=None):
        """
        Generate internal messaging for the project or changes using Claude

        Args:
            project_content (str): JSON string of project content
            changes (dict, optional): Changes detected in the project

        Returns:
            str: JSON string containing the generated internal messaging
        """
        content = self.parse_content(project_content)

        # Format content for Claude
        context = self._format_context(content, changes)

        # Create prompt based on whether we're generating for the whole project or changes
        if not changes:
            prompt = self._create_project_prompt(context)
        else:
            prompt = self._create_changes_prompt(context, changes)

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

        # Combine messaging and objections
        messaging['objections'] = self.parse_content(objections_json)

        return json.dumps(messaging)

    def _create_project_prompt(self, context):
        """Create prompt for generating messaging for the entire project"""

        # 1. Role & Identity Definition
        role = "You are an Internal Communications Strategist with expertise in crafting clear, compelling messages for organizational stakeholders. You excel at translating complex initiatives into concise, actionable communications that drive alignment and engagement."

        # 2. Context & Background
        context_section = f"""
I need to create internal messaging about a project based on the following information:

{context}

This messaging will be used to communicate with internal teams and stakeholders about the project's purpose, value, and impact. It needs to be clear, informative, and focused on business value.
"""

        # 3. Task Definition & Objectives
        task = """
Your task is to generate internal messaging that clearly explains:
1. What the project is
2. The customer pain point it addresses
3. How we're solving it
4. The business impact and value

The messaging should help internal stakeholders understand the project's purpose and importance without requiring extensive background knowledge.
"""

        # 4. Format & Structure Guidelines
        format_guidelines = """
Structure your response as JSON with the following format:
{
    "subject": "Internal Brief: [Project Name]",
    "what_it_is": "Clear description of what the project is (2-3 sentences)",
    "customer_pain": "Description of the customer pain point (2-3 sentences)",
    "our_solution": "Description of our solution approach (2-3 sentences)",
    "business_impact": "Description of the business impact and value (2-3 sentences)"
}

Each section should be concise but informative, avoiding unnecessary jargon while maintaining technical accuracy.
"""

        # 5. Process Instructions
        process = """
Follow these steps to create effective internal messaging:
1. Review all provided information to understand the project's purpose and scope
2. Identify the key customer pain points being addressed
3. Extract the core solution elements and approach
4. Determine the primary business impacts and value drivers
5. Draft clear, concise messaging for each required section
6. Ensure the messaging maintains a balanced view of opportunities and challenges
7. Review for clarity, accuracy, and alignment with organizational communication style
"""

        # 6. Content Requirements
        content_req = """
The messaging must include:
- A clear definition of the project scope and purpose
- Specific customer problems being solved (with metrics when available)
- The core approach or methodology used to address the problem
- Concrete business benefits or outcomes expected
- Technical accuracy while remaining accessible to non-technical stakeholders

The language should be:
- Clear and concise without unnecessary jargon
- Specific rather than generic
- Balanced between optimism and realism
- Action-oriented and focused on outcomes
"""

        # 7. Constraints & Limitations
        constraints = """
Avoid:
- Marketing hype or overly promotional language
- Technical implementation details unnecessary for understanding the concept
- Vague or generic descriptions that could apply to any project
- Focusing on features without connecting them to business value
- Making absolute claims or promises that may be difficult to fulfill
- Downplaying implementation challenges or resource requirements
"""

        # 8. Examples & References
        examples = """
Example of effective internal messaging:

{
    "subject": "Internal Brief: Customer Journey Analytics Platform",
    "what_it_is": "The Customer Journey Analytics Platform is a new data integration and visualization system that connects customer interactions across all touchpoints. It provides a unified view of the customer journey, enabling teams to identify friction points and optimization opportunities.",
    "customer_pain": "Our customers currently struggle to understand how their users navigate across different channels, leading to disjointed experiences and missed conversion opportunities. They lack visibility into the complete customer journey, which makes it difficult to prioritize improvements that will have the greatest impact.",
    "our_solution": "Our solution integrates data from all customer touchpoints into a unified journey map with advanced analytics. It automatically identifies friction points, visualizes conversion paths, and provides actionable recommendations for experience improvements. The platform employs machine learning to predict likely customer behaviors and proactively suggest optimizations.",
    "business_impact": "This initiative will increase our average deal size by 30% by addressing our customers' highest-priority analytics need. It also positions us to expand into the enterprise segment, where journey analytics capabilities are a critical requirement. Initial customer feedback indicates this will significantly improve competitive win rates and customer retention."
}
"""

        # 9. Interaction Guidelines
        interaction = """
This messaging will be shared with internal teams who need to understand and support the project. It should provide enough context that they can explain the project's purpose and value to others, even if they aren't directly involved in its implementation.
"""

        # 10. Quality Assurance
        quality = """
Before finalizing your messaging, verify that:
- All four required sections are complete and focused on their specific purpose
- The messaging accurately reflects the project information provided
- Business value is clearly articulated in concrete terms
- The language is accessible to both technical and business stakeholders
- The messaging maintains a realistic balance between opportunities and challenges
- There is a logical flow between the different sections
"""

        return self.format_prompt(
            role=role,
            context=context_section,
            task=task,
            format_guidelines=format_guidelines,
            process=process,
            content_req=content_req,
            constraints=constraints,
            examples=examples,
            interaction=interaction,
            quality=quality
        )

    def _create_changes_prompt(self, context, changes):
        """Create prompt for generating messaging about project changes"""

        # 1. Role & Identity Definition
        role = "You are an Internal Change Communications Specialist with expertise in communicating project updates, scope changes, and evolving initiatives to organizational stakeholders. You excel at explaining what has changed, why it matters, and how it impacts the business."

        # 2. Context & Background
        context_section = f"""
I need to create internal messaging about changes to a project based on the following information:

{context}

The following changes have been made to the project:
{json.dumps(changes, indent=2)}

This messaging will be used to update internal teams and stakeholders about what has changed in the project and the impact of these changes. It needs to be clear, specific, and focused on what stakeholders need to know.
"""

        # 3. Task Definition & Objectives
        task = """
Your task is to generate internal update messaging that clearly explains:
1. What has changed in the project
2. How these changes impact the customer pain point being addressed
3. The business impact of these changes

The messaging should help internal stakeholders understand the nature and significance of the changes without requiring them to review all project documentation.
"""

        # 4. Format & Structure Guidelines
        format_guidelines = """
Structure your response as JSON with the following format:
{
    "subject": "Internal Update: [Project Name with appropriate update type]",
    "what_changed": "Clear description of what changed in the project (2-4 sentences)",
    "customer_impact": "Description of how changes impact the customer pain point (2-3 sentences)",
    "business_impact": "Description of the business impact of these changes (2-3 sentences)"
}

Each section should be specific to the changes that have occurred, highlighting meaningful shifts rather than minor adjustments.
"""

        # 5. Process Instructions
        process = """
Follow these steps to create effective change messaging:
1. Review the provided changes to understand their nature and scope
2. Assess how these changes affect the project's purpose, approach, or outcomes
3. Determine how the customer experience or pain point resolution is impacted
4. Evaluate the business implications of these changes
5. Draft clear, concise messaging focusing on meaningful changes
6. Ensure the messaging maintains a balanced view of the changes
7. Review for clarity, accuracy, and appropriate tone
"""

        # 6. Content Requirements
        content_req = """
The messaging must include:
- Specific details about what has changed (not just that something changed)
- How these changes affect the customer pain point resolution
- Impact on business outcomes or value
- Rationale for significant changes when apparent from the context
- Any new or modified expectations for internal teams

The language should be:
- Clear and specific about the nature of changes
- Balanced in tone, neither overly optimistic nor pessimistic
- Factual rather than speculative
- Action-oriented where appropriate
"""

        # 7. Constraints & Limitations
        constraints = """
Avoid:
- Vague references to "updates" or "improvements" without specifics
- Technical details that aren't relevant to understanding the impact
- Downplaying significant changes or their implications
- Focusing only on positive aspects if there are also challenges
- Using language that might create unnecessary concern or resistance
- Making commitments or promises about future changes
"""

        # 8. Examples & References
        examples = """
Example of effective change messaging:

{
    "subject": "Internal Update: Customer Portal - Scope Expansion",
    "what_changed": "We've expanded the scope of the Customer Portal project to include self-service analytics capabilities based on user research. This adds three new features to the roadmap: custom report creation, scheduled exports, and visualization tools. The timeline has been extended by six weeks to accommodate these additions.",
    "customer_impact": "These changes directly address the feedback from our enterprise customers that the initial portal scope didn't provide enough data-driven insights. The self-service analytics will enable customers to extract more value from their data without requiring our professional services team, removing a significant pain point in the current workflow.",
    "business_impact": "While this extension affects our timeline, the expanded analytics capabilities increase our projected revenue by approximately 25% through higher-tier subscription adoption. It also reduces the forecasted support ticket volume by 30% as customers will be able to self-serve data needs that currently generate significant support requests."
}
"""

        # 9. Interaction Guidelines
        interaction = """
This messaging will be shared with teams who are already familiar with the project but need to understand recent changes. It should focus on what's different and why it matters, rather than reexplaining the entire project.
"""

        # 10. Quality Assurance
        quality = """
Before finalizing your messaging, verify that:
- The messaging focuses specifically on what has changed, not general project information
- Changes are described concretely, not in vague or generic terms
- Both opportunities and challenges from the changes are addressed
- The business impact section includes specific outcomes or metrics where possible
- The tone is informative and balanced, neither overly promotional nor negative
"""

        return self.format_prompt(
            role=role,
            context=context_section,
            task=task,
            format_guidelines=format_guidelines,
            process=process,
            content_req=content_req,
            constraints=constraints,
            examples=examples,
            interaction=interaction,
            quality=quality
        )

    def _format_context(self, content, changes=None):
        """Format content as context for Claude"""
        context = []

        # Add PRD information
        prd = content.get('prd', {})
        if prd:
            context.append("== Product Requirements Document (PRD) ==")
            for key, value in prd.items():
                if isinstance(value, str) and value:
                    context.append(f"{key.replace('_', ' ').title()}: {value}")

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

        # Add changes information if provided
        if changes:
            context.append("\n== Recent Changes ==")
            for doc_type, doc_changes in changes.items():
                context.append(f"\nChanges to {doc_type}:")
                if doc_changes.get('added'):
                    context.append(f"Added: {', '.join(doc_changes['added'])}")
                if doc_changes.get('modified'):
                    context.append(f"Modified: {', '.join(doc_changes['modified'])}")
                if doc_changes.get('removed'):
                    context.append(f"Removed: {', '.join(doc_changes['removed'])}")

        return "\n".join(context)

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
        strategy = content.get('strategy', {})

        # Extract key points
        project_name = prd.get('name', 'Project')
        overview = prd.get('overview', '')
        pain_points = prd.get('problem_statement', '')
        solution = prd.get('solution', '')
        business_value = strategy.get('business_value', '')

        # Format the messaging
        messaging = {
            'subject': f"Internal Brief: {project_name}",
            'what_it_is': f"{project_name} is our initiative to {overview[:150]}...",
            'customer_pain': f"Our customers are struggling with {pain_points[:150]}...",
            'our_solution': f"We're addressing this by {solution[:150]}...",
            'business_impact': f"This initiative will {business_value[:150] if business_value else 'improve our customer experience and drive business growth'}...",
            'objections': [
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
            ]
        }

        return json.dumps(messaging)

    def _generate_change_messaging(self, content, changes):
        """Generate messaging for project changes"""
        prd = content.get('prd', {})

        # Extract project name
        project_name = prd.get('name', 'Project')

        # Determine the nature of the changes
        has_prd_changes = self._has_changes(changes.get('prd', {}))
        has_ticket_changes = self._has_changes(changes.get('tickets', {}))
        has_strategy_changes = self._has_changes(changes.get('strategy', {}))

        # Generate appropriate subject line
        subject = f"Internal Update: {project_name} "
        if has_strategy_changes:
            subject += "Strategy Changes"
        elif has_prd_changes:
            subject += "Scope Update"
        elif has_ticket_changes:
            subject += "Implementation Update"
        else:
            subject += "Minor Update"

        # Generate messaging about the changes
        what_changed = self._describe_changes(changes)
        customer_impact = self._describe_customer_impact(content, changes)
        business_impact = self._describe_business_impact(content, changes)

        # Format the messaging
        messaging = {
            'subject': subject,
            'what_changed': what_changed,
            'customer_impact': customer_impact,
            'business_impact': business_impact,
            'objections': [
                {
                    "title": "Change Justification Insufficient",
                    "explanation": "The messaging doesn't adequately explain why these changes were necessary. Without a clear rationale, stakeholders may question if these changes represent scope creep rather than strategic adjustments."
                },
                {
                    "title": "Timeline Impact Understated",
                    "explanation": "The messaging doesn't clearly address how these changes will affect project timelines. Stakeholders need transparency about potential delays to manage dependencies and expectations."
                },
                {
                    "title": "Cross-team Coordination Requirements",
                    "explanation": "The messaging doesn't address the coordination needed between teams to implement these changes. This could lead to implementation gaps if teams aren't properly aligned on their responsibilities."
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
                descriptions.append(f"Added {len(prd_changes['added'])} new sections to the PRD")
            if prd_changes.get('modified'):
                descriptions.append(f"Updated {len(prd_changes['modified'])} sections in the PRD")
            if prd_changes.get('removed'):
                descriptions.append(f"Removed {len(prd_changes['removed'])} sections from the PRD")

        # Describe ticket changes
        ticket_changes = changes.get('tickets', {})
        if self._has_changes(ticket_changes):
            if ticket_changes.get('added'):
                descriptions.append(f"Added {len(ticket_changes['added'])} new tickets")
            if ticket_changes.get('modified'):
                descriptions.append(f"Updated {len(ticket_changes['modified'])} existing tickets")
            if ticket_changes.get('removed'):
                descriptions.append(f"Closed {len(ticket_changes['removed'])} tickets")

        # Describe strategy changes
        strategy_changes = changes.get('strategy', {})
        if self._has_changes(strategy_changes):
            if strategy_changes.get('added') or strategy_changes.get('modified'):
                descriptions.append("Updated project strategy")

        if not descriptions:
            descriptions.append("Made minor updates to project documentation")

        return ". ".join(descriptions)

    def _describe_customer_impact(self, content, changes):
        """Describe how changes impact the customer"""
        prd = content.get('prd', {})
        pain_points = prd.get('problem_statement', '')

        if self._has_changes(changes.get('strategy', {})):
            return f"These changes refine our approach to solving the customer pain point of {pain_points[:100]}..."
        elif self._has_changes(changes.get('prd', {})):
            return f"These updates improve our solution to the customer pain point of {pain_points[:100]}..."
        else:
            return "These changes maintain our focus on addressing key customer pain points."

    def _describe_business_impact(self, content, changes):
        """Describe business impact of the changes"""
        strategy = content.get('strategy', {})
        business_value = strategy.get('business_value', '')

        if business_value:
            return f"These changes help us achieve {business_value[:150]}..."
        else:
            return "These changes support our business objectives and customer satisfaction goals."