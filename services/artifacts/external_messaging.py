# services/artifacts/external_messaging.py
import json
import logging
from models import Project
from flask import current_app
import anthropic

class ExternalMessagingGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_latest(self):
        """Get the latest generated external messaging"""
        project = Project.query.order_by(Project.timestamp.desc()).first()
        if project and project.external_messaging:
            return json.loads(project.external_messaging)
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
        content = json.loads(project_content)

        # Initialize Claude client
        try:
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
            self.logger.error(f"Error generating external messaging with Claude: {str(e)}")
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

    def _create_project_prompt(self, context):
        """Create prompt for generating messaging for the entire project"""
        return f"""
        I need to create external messaging for customers about a project based on the following information:

        {context}

        Please generate customer-facing messaging that explains:
        1. The pain point the customer is experiencing
        2. How our solution addresses it
        3. The benefits they'll receive

        Format the response as JSON with the following structure:
        {{
            "headline": "Introducing [Project Name]",
            "pain_point": "Description of the customer pain point",
            "solution": "Description of our solution",
            "benefits": "Description of the benefits to the customer"
        }}

        The messaging should be clear, concise, benefit-focused, and suitable for external communication with customers.
        """

    def _create_changes_prompt(self, context, changes):
        """Create prompt for generating messaging about project changes"""
        return f"""
        I need to create external messaging about changes to a product based on the following information:

        {context}

        The following changes have been made:
        {json.dumps(changes, indent=2)}

        Please generate customer-facing messaging that explains:
        1. What has changed or been added
        2. How this addresses their pain point
        3. A call to action

        Format the response as JSON with the following structure:
        {{
            "headline": "[Project Name] Update: [Key Benefit]",
            "pain_point": "Reminder of the pain point being addressed",
            "solution": "How the update/changes solve the problem",
            "call_to_action": "Call to action for customers"
        }}

        The messaging should be clear, concise, benefit-focused, and suitable for external communication with customers.
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
            'benefits': "This will help you " + (benefits[0][:100] + "..." if benefits else "save time and improve your workflow.")
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
            'call_to_action': f"Try the latest version of {project_name} today."
        }

        return json.dumps(messaging)

    def _has_changes(self, doc_changes):
        """Check if a document has any changes"""
        return (
            len(doc_changes.get('added', [])) > 0 or 
            len(doc_changes.get('modified', [])) > 0 or 
            len(doc_changes.get('removed', [])) > 0
        )