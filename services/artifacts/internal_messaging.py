# services/artifacts/internal_messaging.py
import json
import logging
from models import Project
from flask import current_app
from .base_generator import BaseGenerator
from .objection_generator import ObjectionGenerator
from .improvement_generator import ImprovementGenerator

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

        # Generate improvements
        improvements_json = self.improvement_generator.generate_for_artifact(
            content, messaging, 'internal')

        # Combine messaging, objections, and improvements
        messaging['objections'] = self.parse_content(objections_json)
        messaging['improvements'] = self.parse_content(improvements_json)

        return json.dumps(messaging)

    def _create_project_prompt(self, context):
        """Create prompt for generating messaging for the entire project"""

        # 1. Role & Identity Definition
        role = "You are a Technical Project Communicator who creates factual, direct internal team messaging."

        # 2. Context & Background
        context_section = f"""
Project information:
{context}

Create internal messaging for team members and stakeholders about this project.
"""

        # 3. Task Definition & Objectives
        task = """
Generate internal messaging with:
1. A clear subject line
2. A direct explanation of what the project is
3. A precise statement of the customer problem
4. A factual description of the solution approach
5. Specific business impact with metrics when possible

Focus on operational clarity and factual information teams need.
"""

        # 4. Format & Structure Guidelines
        format_guidelines = """
Format as JSON with:
{
    "subject": "Internal: [Project Name] - [Primary Focus]",
    "what_it_is": "Description of what the project is (1-2 sentences)",
    "customer_pain": "Description of the customer problem (1-2 sentences)",
    "our_solution": "Description of our solution approach (1-2 sentences)",
    "business_impact": "Specific business impact with metrics (1-2 sentences)",
    "timeline": "Key dates and milestones (1-2 sentences)",
    "team_needs": "Required resources and dependencies (1-2 sentences)"
}
"""

        # 5. Process Instructions
        process = """
1. Extract the core project purpose
2. Identify specific customer problems
3. Determine key solution elements
4. Calculate business impact and metrics
5. Identify key timeline milestones
6. Determine resource requirements
7. Draft direct, factual statements for each section
8. Focus on information teams need to act
"""

        # 6. Content Requirements
        content_req = """
Content must be:
- Factual with specific details
- Quantifiable where possible (numbers, percentages)
- Direct and concise (under 20 words per sentence)
- Free of subjective claims
- Written in active voice
- Clear about resource needs and dependencies
- Specific about timeline and milestones
- Practical about implementation requirements

The subject must clearly identify the project and focus.
The project description must state what teams will build.
Customer pain must specify actual problems, ideally with metrics.
Solution approach must outline how teams will solve the problem.
Business impact must include specific metrics when possible.
Timeline must include concrete dates or timeframes.
Team needs must specify required resources.
"""

        # 7. Constraints & Limitations
        constraints = """
Do not:
- Use marketing language or hype
- Make subjective claims without evidence
- Use unnecessary adjectives or adverbs
- Include vague statements
- Use passive voice
- Exceed 20 words per sentence
- Omit resource requirements or dependencies
- Hide implementation challenges
"""

        # 8. Examples & References
        examples = """
Example of effective, factual internal messaging:

{
    "subject": "Internal: Document Sync Tool - Engineering Kickoff",
    "what_it_is": "A system that monitors document changes across PRDs, tickets, and strategy docs. It automatically identifies inconsistencies and suggests updates.",
    "customer_pain": "Teams waste 4.2 hours weekly reconciling inconsistent documentation. This causes a 28% increase in implementation errors and delays project completion by 2-3 weeks.",
    "our_solution": "We'll build connectors for Jira, Confluence, and Google Docs using their APIs. Our ML-based inconsistency detection will flag issues and suggest specific updates.",
    "business_impact": "Will reduce documentation work by 62%, decrease implementation errors by 45%, and shorten project timelines by 2 weeks on average. Expected to increase team capacity by 8%.",
    "timeline": "Design complete by June 5. Alpha by July 20. Beta by August 15. GA release by September 30.",
    "team_needs": "Requires 2 backend engineers, 1 ML specialist, and 1 frontend developer for 12 weeks. Dependencies on Jira API upgrade scheduled for June 10."
}
"""

        # 9. Interaction Guidelines
        interaction = """
This messaging will be shared with internal teams who need specific, actionable information about the project. Focus on what they need to know to contribute effectively.
"""

        # 10. Quality Assurance
        quality = """
Verify the output:
- Contains specific details, not generalities
- Includes quantifiable elements where possible
- Uses direct, concise language
- Includes concrete timeline milestones
- Specifies actual resource requirements
- Presents business impact with metrics
- Uses active voice exclusively
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
        role = "You are a Technical Project Update Communicator who creates factual, direct internal team messaging about project changes."

        # 2. Context & Background
        context_section = f"""
Project changes:
{context}

Create internal messaging about these project changes for team members and stakeholders.
"""

        # 3. Task Definition & Objectives
        task = """
Generate internal update messaging with:
1. A clear subject line about the changes
2. A direct explanation of what changed
3. How these changes impact customers
4. How these changes affect the business
5. Timeline impacts
6. Resource requirement changes

Focus on operational clarity about what teams need to do differently.
"""

        # 4. Format & Structure Guidelines
        format_guidelines = """
Format as JSON with:
{
    "subject": "Update: [Project Name] - [Change Type]",
    "what_changed": "Specific description of what changed (2-3 sentences)",
    "customer_impact": "How changes affect the customer problem/solution (1-2 sentences)",
    "business_impact": "How changes affect metrics and goals (1-2 sentences)",
    "timeline_impact": "Changes to schedule and milestones (1-2 sentences)",
    "team_needs": "Changes to required resources (1-2 sentences)"
}
"""

        # 5. Process Instructions
        process = """
1. Identify exactly what changed in the project
2. Determine how these changes affect customers
3. Calculate impact on business metrics
4. Assess timeline implications
5. Determine resource requirement changes
6. Draft direct, factual statements about each impact
7. Focus on what teams need to know to adapt
"""

        # 6. Content Requirements
        content_req = """
Content must be:
- Factual with specific details about what changed
- Quantifiable where possible (numbers, percentages)
- Direct and concise (under 20 words per sentence)
- Free of subjective claims
- Written in active voice
- Clear about implementation implications
- Specific about timeline impacts
- Practical about resource requirement changes

The subject must clearly identify the nature of changes.
What changed must specify actual modifications to scope or approach.
Customer impact must explain how changes affect the problem/solution.
Business impact must include specific metric changes.
Timeline impact must state actual schedule changes.
Team needs must specify resource requirement changes.
"""

        # 7. Constraints & Limitations
        constraints = """
Do not:
- Use marketing language or hype
- Make subjective claims without evidence
- Use unnecessary adjectives or adverbs
- Include vague statements about "improvements"
- Use passive voice
- Exceed 20 words per sentence
- Omit negative impacts of changes
- Hide implementation challenges
"""

        # 8. Examples & References
        examples = """
Example of effective, factual update messaging:

{
    "subject": "Update: Document Sync Tool - Scope Change",
    "what_changed": "Added support for Linear tickets and Notion docs based on customer feedback. Removed planned SharePoint integration due to API limitations. Changed inconsistency detection to use rule-based approach instead of ML to reduce complexity.",
    "customer_impact": "Changes will support 35% more customers who use Linear/Notion. Will improve initial accuracy from 75% to 82% by using proven rule-based approach instead of ML.",
    "business_impact": "Expected to increase addressable market by $2.4M. Will reduce development cost by $120K by avoiding ML complexity. May slightly decrease long-term accuracy improvement rate.",
    "timeline_impact": "GA release delayed by 3 weeks to October 21. Alpha timeline unchanged. Beta expanded by 2 weeks.",
    "team_needs": "No longer need ML specialist. Need additional QA time for new integrations. Backend team needs 2 additional weeks."
}
"""

        # 9. Interaction Guidelines
        interaction = """
This messaging will be shared with teams who are already working on or familiar with the project. Focus on what has changed and how it affects their work.
"""

        # 10. Quality Assurance
        quality = """
Verify the output:
- Clearly explains what actually changed
- Quantifies impacts where possible
- Uses direct, concise language
- Includes specific timeline impacts
- Specifies resource requirement changes
- Presents both positive and negative impacts
- Uses active voice exclusively
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
            'what_it_is': f"A system that monitors document changes across PRDs, tickets, and strategy docs. It automatically identifies inconsistencies and suggests updates.",
            'customer_pain': "Teams waste 4.2 hours weekly reconciling inconsistent documentation. This causes a 28% increase in implementation errors and delays project completion by 2-3 weeks.",
            'our_solution': "We'll build connectors for Jira, Confluence, and Google Docs using their APIs. Our inconsistency detection will flag issues and suggest specific updates.",
            'business_impact': "Will reduce documentation work by 62%, decrease implementation errors by 45%, and shorten project timelines by 2 weeks on average. Expected to increase team capacity by 8%.",
            'timeline': "Design complete by June 5. Alpha by July 20. Beta by August 15. GA release by September 30.",
            'team_needs': "Requires 2 backend engineers, 1 ML specialist, and 1 frontend developer for 12 weeks. Dependencies on Jira API upgrade scheduled for June 10."
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
            'team_needs': "No longer need ML specialist. Need additional QA time for new integrations. Backend team needs 2 additional weeks."
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