# services/artifacts/internal_messaging.py
import json
import logging
from models import Project
from flask import current_app
import anthropic

class InternalMessagingGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_latest(self):
        """Get the latest generated internal messaging"""
        project = Project.query.order_by(Project.timestamp.desc()).first()
        if project and project.internal_messaging:
            return json.loads(project.internal_messaging)
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
        content = json.loads(project_content)

        # Initialize Claude client
        try:
            # Call Claude
            response = client.messages.create(
                model=model,
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract and parse the response
            response_text = response.content[0].text

            # Find JSON in the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start != -1 and json_end != -1:
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)
                return json.dumps(result)
            else:
                self.logger.error("Could not find JSON in Claude response")
                return self._rule_based_generation(content, changes)

        except Exception as e:
            self.logger.error(f"Error generating internal messaging with Claude: {str(e)}")
            # Fall back to rule-based generation
            return self._rule_based_generation(content, changes)

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

    def _create_project_prompt(self, context):
        """Create prompt for generating messaging for the entire project"""
        return f"""
        I need to create internal messaging for a project based on the following information:

        {context}

        Please generate internal messaging that explains:
        1. What the project is
        2. The customer pain point it addresses
        3. How we're solving it
        4. The business impact

        Format the response as JSON with the following structure:
        {{
            "subject": "Internal Brief: [Project Name]",
            "what_it_is": "Description of what the project is",
            "customer_pain": "Description of the customer pain point",
            "our_solution": "Description of our solution approach",
            "business_impact": "Description of the business impact"
        }}

        The messaging should be clear, concise, and suitable for internal stakeholders.
        """

    def _create_changes_prompt(self, context, changes):
        """Create prompt for generating messaging about project changes"""
        return f"""
        I need to create internal messaging about changes to a project based on the following information:

        {context}

        The following changes have been made:
        {json.dumps(changes, indent=2)}

        Please generate internal messaging that explains:
        1. What has changed in the project
        2. How these changes impact the customer pain point
        3. The business impact of these changes

        Format the response as JSON with the following structure:
        {{
            "subject": "Internal Update: [Project Name with appropriate update type]",
            "what_changed": "Description of what changed",
            "customer_impact": "Description of how changes impact the customer pain point",
            "business_impact": "Description of the business impact of these changes"
        }}

        The messaging should be clear, concise, and suitable for internal stakeholders.
        """

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
            'business_impact': f"This initiative will {business_value[:150] if business_value else 'improve our customer experience and drive business growth'}..."
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
            'business_impact': business_impact
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
            api_key = current_app.config.get('CLAUDE_API_KEY')
            model = current_app.config.get('CLAUDE_MODEL', 'claude-3-opus-20240229')
            client = anthropic.Anthropic(api_key=api_key)
        except Exception as e:
            self.logger.error(f"Error initializing Claude client: {str(e)}")
            # Fall back to rule-based generation if Claude is unavailable
            return self._rule_based_generation(content, changes)

        # Format content for Claude
        context = self._format_context(content, changes)

        # Determine if we're generating for the whole project or for changes
        if not changes:
            prompt = self._create_project_prompt(context)
        else:
            prompt = self._create_changes_prompt(context, changes)

        try: