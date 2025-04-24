# services/artifacts/external_messaging.py
import json
import logging
from models import Project
from flask import current_app
from .base_generator import BaseGenerator
from .objection_generator import ObjectionGenerator

class ExternalMessagingGenerator(BaseGenerator):
    """
    Generator for external messaging about the project.

    This service creates messaging for external audiences (customers)
    about the pain point the project addresses, how the solution works,
    and the benefits customers will receive.
    """

    def __init__(self):
        """Initialize the generator with a logger and objection generator."""
        super().__init__()
        self.objection_generator = ObjectionGenerator()

    def get_latest(self):
        """Get the latest generated external messaging"""
        project = Project.query.order_by(Project.timestamp.desc()).first()
        if project and project.external_messaging:
            result = project.get_external_messaging_dict()

            # Add objections if available
            if project.external_objections:
                result['objections'] = project.get_external_objections_list()

            return result
        return None

    def generate(self, project_content, changes=None):
        """
        Generate external messaging for the project or changes using Claude

        Args:
            project_content (str): JSON string of project content
            changes (dict, optional): Changes detected in the project

        Returns:
            str: JSON string containing the generated external messaging
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
            content, messaging, 'external')

        # Combine messaging and objections
        messaging['objections'] = self.parse_content(objections_json)

        return json.dumps(messaging)

    def _create_project_prompt(self, context):
        """Create prompt for generating messaging for the entire project"""

        # 1. Role & Identity Definition
        role = "You are a Customer-Focused Communications Specialist with expertise in translating technical solutions into compelling, benefit-oriented messaging for end users. You excel at articulating pain points clearly and communicating value propositions that resonate with customer needs."

        # 2. Context & Background
        context_section = f"""
I need to create external messaging for customers about a product or service based on the following information:

{context}

This messaging will be used in customer-facing communications to explain the value proposition, highlight how it addresses their pain points, and motivate them to engage with our solution. It needs to be clear, compelling, and focused on customer benefits.
"""

        # 3. Task Definition & Objectives
        task = """
Your task is to generate customer-facing messaging that effectively:
1. Captures attention with a compelling headline
2. Clearly articulates the pain point the customer is experiencing
3. Explains how our solution addresses this pain point
4. Describes the concrete benefits customers will receive

The messaging should motivate potential customers to learn more about our solution by addressing their needs directly and offering clear value.
"""

        # 4. Format & Structure Guidelines
        format_guidelines = """
Structure your response as JSON with the following format:
{
    "headline": "Introducing [Project Name]: [Key Benefit]",
    "pain_point": "Description of the customer pain point (2-3 sentences)",
    "solution": "Description of how our solution addresses it (2-3 sentences)",
    "benefits": "Description of the benefits customers will receive (2-3 sentences)",
    "call_to_action": "Brief call to action for customers (1 sentence)"
}

Each section should be concise, compelling, and focused on the customer perspective.
"""

        # 5. Process Instructions
        process = """
Follow these steps to create effective external messaging:
1. Review all provided information to understand the customer problems and our solution
2. Identify the most compelling pain points from a customer perspective
3. Extract the key solution elements that directly address these pain points
4. Determine the most meaningful benefits for customers
5. Craft a headline that focuses on a key benefit or outcome
6. Draft each section to build a cohesive narrative from problem to solution
7. Create a clear call to action that motivates next steps
8. Review for clarity, persuasiveness, and customer focus
"""

        # 6. Content Requirements
        content_req = """
The messaging must include:
- A benefit-focused headline that captures attention
- A clear articulation of the customer problem or pain point
- A straightforward explanation of how our solution works
- Specific, tangible benefits customers will receive
- A call to action that encourages next steps

The language should be:
- Customer-focused rather than company-focused
- Benefit-oriented rather than feature-oriented
- Clear and accessible without unnecessary jargon
- Specific rather than generic
- Conversational but professional in tone
"""

        # 7. Constraints & Limitations
        constraints = """
Avoid:
- Technical jargon or internal terminology that customers won't understand
- Features without clear connection to benefits
- Vague claims or generic statements that could apply to any solution
- Overpromising or making unsubstantiated claims
- Company-focused language (excessive use of "we" instead of "you")
- Focusing on details that don't matter to customers
"""

        # 8. Examples & References
        examples = """
Example of effective external messaging:

{
    "headline": "Introducing DataFlow: Transform Data Chaos into Customer Insights",
    "pain_point": "You're collecting mountains of customer data, but extracting meaningful insights remains frustratingly complex and time-consuming. Your teams spend hours manually connecting data points across systems, yet still struggle to get a complete picture of customer behavior.",
    "solution": "DataFlow automatically connects and standardizes customer data from all your sources into a unified customer view. Our intelligent system identifies patterns, surfaces insights, and makes predictions about customer behavior without requiring data science expertise.",
    "benefits": "Make confident decisions based on complete customer insights in minutes, not days. Identify your highest-value opportunities and potential churn risks before they become obvious. Free your teams from manual data tasks to focus on creating exceptional customer experiences.",
    "call_to_action": "Book a demo today to see how DataFlow can transform your customer data into your competitive advantage."
}
"""

        # 9. Interaction Guidelines
        interaction = """
This messaging will be used in customer-facing materials where we often have limited time to capture attention and convey value. It should quickly establish relevance to the customer's situation and present a clear path to improvement through our solution.
"""

        # 10. Quality Assurance
        quality = """
Before finalizing your messaging, verify that:
- The headline clearly communicates a key benefit
- The pain point description will resonate with the target audience
- The solution explanation is easy to understand without technical background
- Benefits are specific and meaningful to customers
- All language is customer-focused rather than company-focused
- The messaging builds a logical flow from problem to solution to outcome
- The call to action is clear and motivating
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
        role = "You are a Customer Update Communications Specialist with expertise in crafting clear, benefit-focused messaging about product changes and updates. You excel at explaining how new features or improvements address customer needs and deliver additional value."

        # 2. Context & Background
        context_section = f"""
I need to create external messaging about updates or changes to a product or service based on the following information:

{context}

The following changes have been made:
{json.dumps(changes, indent=2)}

This messaging will be used to communicate with existing customers about what has changed and how these changes benefit them. It needs to be clear, specific, and focused on the value these changes deliver.
"""

        # 3. Task Definition & Objectives
        task = """
Your task is to generate customer-facing update messaging that effectively:
1. Captures attention with a headline about the update
2. Reminds customers of the pain point being addressed
3. Explains how the changes or updates enhance the solution
4. Provides a clear call to action

The messaging should help customers understand the value of the updates and motivate them to engage with the improved solution.
"""

        # 4. Format & Structure Guidelines
        format_guidelines = """
Structure your response as JSON with the following format:
{
    "headline": "[Project Name] Update: [Key Benefit]",
    "pain_point": "Reminder of the pain point being addressed (1-2 sentences)",
    "solution": "How the update/changes enhance the solution (2-3 sentences)",
    "call_to_action": "Call to action for customers (1 sentence)"
}

Each section should be concise, specific to the changes, and focused on customer benefits.
"""

        # 5. Process Instructions
        process = """
Follow these steps to create effective update messaging:
1. Review the provided changes to understand what's new or different
2. Identify how these changes improve the solution for customers
3. Determine which customer pain points are better addressed with these changes
4. Craft a headline that focuses on the key improvement or benefit
5. Briefly remind customers of the core problem being solved
6. Explain specifically how the updates enhance the solution
7. Create a call to action appropriate for existing customers
8. Review for clarity, specificity, and customer benefit focus
"""

        # 6. Content Requirements
        content_req = """
The messaging must include:
- A headline that highlights the key benefit of the update
- A brief reminder of the customer problem being solved
- A clear explanation of how the changes improve the solution
- Specific benefits customers will experience from the updates
- A call to action that encourages appropriate next steps

The language should be:
- Specific about what has changed and why it matters
- Customer-focused, emphasizing benefits over features
- Clear and accessible without unnecessary jargon
- Positive and forward-looking
- Conversational but professional in tone
"""

        # 7. Constraints & Limitations
        constraints = """
Avoid:
- Technical details that aren't relevant to the customer experience
- Vague references to "improvements" without explaining the benefit
- Focusing on changes that don't deliver meaningful customer value
- Company-focused language that emphasizes effort rather than results
- Requiring customers to understand previous versions to appreciate updates
- Creating unnecessary urgency or pressure to act
"""

        # 8. Examples & References
        examples = """
Example of effective update messaging:

{
    "headline": "TaskMaster Update: Complete Projects 30% Faster with Smart Automation",
    "pain_point": "Managing complex projects across multiple team members often leads to bottlenecks, missed deadlines, and endless status meetings.",
    "solution": "Our latest update introduces Smart Automation that automatically assigns tasks based on team member availability and skills. The new visual workflow builder allows you to create custom automation rules without coding, while intelligent deadline predictions help prevent schedule slippage before it happens.",
    "call_to_action": "Log in today to enable Smart Automation and start accelerating your projects."
}
"""

        # 9. Interaction Guidelines
        interaction = """
This messaging will be shared with existing customers who are already familiar with the core product or service. It should focus on what's new and the additional value these changes deliver, rather than reexplaining the entire value proposition.
"""

        # 10. Quality Assurance
        quality = """
Before finalizing your messaging, verify that:
- The headline communicates a specific benefit from the updates
- The messaging clearly explains what has changed
- Changes are connected directly to customer benefits
- The tone is positive and customer-focused
- The call to action is clear and appropriate for existing customers
- The messaging would make sense to someone already using the product
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

        # Add changes information if provided
        if changes:
            context.append("\n== Recent Changes ==")
            for doc_type, doc_changes in changes.items():
                if doc_type == 'prd':
                    context.append(f"\nChanges to product requirements:")
                    if doc_changes.get('added'):
                        context.append(f"Added features: {', '.join(doc_changes['added'])}")
                    if doc_changes.get('modified'):
                        context.append(f"Updated features: {', '.join(doc_changes['modified'])}")

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
        prfaq = content.get('prfaq', {})

        # Extract key points
        project_name = prd.get('name', 'Project')
        pain_points = prd.get('problem_statement', '')
        solution = prd.get('solution', '')
        benefits = []

        # Look for benefits in PRFAQ
        if 'frequently_asked_questions' in prfaq:
            for qa in prfaq['frequently_asked_questions']:
                if 'benefit' in qa.get('question', '').lower():
                    benefits.append(qa.get('answer', ''))

        # Format the messaging
        messaging = {
            'headline': f"Introducing {project_name}",
            'pain_point': f"We know you've been struggling with {pain_points[:100]}...",
            'solution': f"That's why we built {project_name}, which {solution[:100]}...",
            'benefits': "This will help you " + (benefits[0][:100] + "..." if benefits else "save time and improve your workflow."),
            'call_to_action': f"Learn how {project_name} can transform your experience today.",
            'objections': [
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
            ]
        }

        return json.dumps(messaging)

    def _generate_change_messaging(self, content, changes):
        """Generate messaging for project changes"""
        prd = content.get('prd', {})

        # Extract project name
        project_name = prd.get('name', 'Project')

        # Determine if this is a new feature or an update
        is_new_feature = False
        if self._has_changes(changes.get('prd', {})):
            if changes['prd'].get('added'):
                is_new_feature = True

        # Generate appropriate headline
        if is_new_feature:
            headline = f"New in {project_name}: "
            if changes['prd'].get('added'):
                section = changes['prd']['added'][0]
                headline += section.replace('_', ' ').title()
        else:
            headline = f"{project_name} Update: Improved Experience"

        # Extract pain point and solution
        pain_point = prd.get('problem_statement', '')
        solution = prd.get('solution', '')

        # Format the messaging
        messaging = {
            'headline': headline,
            'pain_point': f"We heard your feedback about {pain_point[:100]}...",
            'solution': f"We've updated {project_name} to {solution[:100]}...",
            'call_to_action': f"Try the latest version of {project_name} today.",
            'objections': [
                {
                    "title": "Update Benefits Unclear",
                    "explanation": "The messaging doesn't specifically explain how these updates deliver new or enhanced value to customers. Without clear benefits tied to the changes, customers may not see a reason to explore the update."
                },
                {
                    "title": "Transition Concerns Unaddressed",
                    "explanation": "The messaging doesn't address potential concerns about migrating to the updated version, such as learning curve, data migration, or compatibility with existing workflows."
                },
                {
                    "title": "Lacks Specific Improvements",
                    "explanation": "The messaging uses general terms like 'improved experience' rather than naming specific enhancements that customers will recognize as valuable to their needs."
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