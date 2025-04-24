# services/artifacts/internal_messaging.py
import json
import logging
import re
import requests
from models import Project
from flask import current_app

# Import prompt function
try:
    from prompts import get_prompt
except ImportError:
    # Fallback if prompts.py isn't available
    def get_prompt(prompt_type, context, **kwargs):
        return f"Generate internal messaging based on: {context}"

class InternalMessagingGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_latest(self):
        """Get the latest generated internal messaging"""
        project = Project.query.order_by(Project.timestamp.desc()).first()
        if project and project.internal_messaging:
            return json.loads(project.internal_messaging)
        return None

    def generate(self, project_content, changes=None, use_moo=False):
        """
        Generate internal messaging for the project or changes

        Args:
            project_content (str): JSON string of project content
            changes (dict, optional): Changes detected in the project
            use_moo (bool): Whether to include Most Obvious Objections

        Returns:
            str: JSON string containing the generated internal messaging
        """
        # Always set use_moo to True
        use_moo = True
        
        # Parse content
        content = json.loads(project_content)

        # Clean any markdown in the content
        self._clean_markdown_in_content(content)

        # Try to use Claude via direct HTTP first
        try:
            # Check if Claude API key is available
            if current_app.config.get('CLAUDE_API_KEY'):
                # Format content for Claude
                context = self._format_context(content, changes)

                # Get project name for prompt context
                project_name = content.get('prd', {}).get('name', 'Project Alignment Tool')

                # Determine which prompt to use based on changes and moo
                if changes:
                    prompt_type = 'internal_changes_moo' if use_moo else 'internal_changes'
                    prompt = get_prompt(prompt_type, context, project_name=project_name, changes=json.dumps(changes, indent=2))
                else:
                    prompt_type = 'internal_messaging_moo' if use_moo else 'internal_messaging'
                    prompt = get_prompt(prompt_type, context, project_name=project_name)

                # Call Claude API
                claude_response = self._call_claude_api(prompt)

                # If we got a response, extract JSON and return it
                if claude_response:
                    json_start = claude_response.find('{')
                    json_end = claude_response.rfind('}') + 1

                    if json_start != -1 and json_end != -1:
                        json_str = claude_response[json_start:json_end]
                        try:
                            result = json.loads(json_str)
                            return json.dumps(result)
                        except json.JSONDecodeError:
                            self.logger.error("Failed to parse JSON from Claude response")
        except Exception as e:
            self.logger.error(f"Error using Claude: {str(e)}")

        # Fall back to rule-based generation
        if not changes:
            return self._generate_project_messaging(content)
        else:
            return self._generate_change_messaging(content, changes)

    def _call_claude_api(self, prompt):
        """Call Claude API directly using HTTP requests"""
        api_key = current_app.config.get('CLAUDE_API_KEY')
        if not api_key:
            return None

        headers = {
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        }

        data = {
            'model': current_app.config.get('CLAUDE_MODEL', 'claude-3-opus-20240229'),
            'max_tokens': 1000,
            'messages': [
                {'role': 'user', 'content': prompt}
            ]
        }

        try:
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()
            return result['content'][0]['text']
        except Exception as e:
            self.logger.error(f"Error calling Claude API: {e}")
            return None

    def _clean_markdown_in_content(self, content):
        """Clean any markdown formatting in the content dictionary"""
        prd = content.get('prd', {})

        # Clean each string field in the PRD
        for key, value in prd.items():
            if isinstance(value, str):
                prd[key] = self._clean_markdown(value)

        # Clean PRFAQ if exists
        prfaq = content.get('prfaq', {})
        if 'press_release' in prfaq and isinstance(prfaq['press_release'], str):
            prfaq['press_release'] = self._clean_markdown(prfaq['press_release'])

        if 'frequently_asked_questions' in prfaq:
            for qa in prfaq['frequently_asked_questions']:
                if 'question' in qa and isinstance(qa['question'], str):
                    qa['question'] = self._clean_markdown(qa['question'])
                if 'answer' in qa and isinstance(qa['answer'], str):
                    qa['answer'] = self._clean_markdown(qa['answer'])

        # Clean strategy if exists
        strategy = content.get('strategy', {})
        for key, value in strategy.items():
            if isinstance(value, str):
                strategy[key] = self._clean_markdown(value)

    def _clean_markdown(self, text):
        """Remove markdown formatting from text"""
        if not text:
            return text

        # Remove markdown headers
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

        # Remove markdown list markers
        text = re.sub(r'^\s*[\*\-\+]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

        # Remove markdown emphasis
        text = re.sub(r'[*_]{1,2}(.*?)[*_]{1,2}', r'\1', text)

        # Remove markdown code blocks and inline code
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`(.*?)`', r'\1', text)

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Remove leading/trailing whitespace
        text = text.strip()

        return text

    def _format_context(self, content, changes=None):
        """Format content as context for Claude"""
        context = []

        # Add PRD information
        prd = content.get('prd', {})
        if prd:
            context.append("== Product Requirements Document (PRD) ==")

            # Get project name and context
            project_name = prd.get('name', 'Project Alignment Tool')
            context.append(f"Project Name: {project_name}")

            # Add overview with more context
            if prd.get('overview'):
                context.append(f"Overview: {prd.get('overview')}")

            # Add problem statement if available
            if prd.get('problem_statement'):
                context.append(f"Problem Statement: {prd.get('problem_statement')}")

            # Add solution if available
            if prd.get('solution'):
                context.append(f"Solution: {prd.get('solution')}")

            # Add any other fields
            for key, value in prd.items():
                if key not in ['name', 'overview', 'problem_statement', 'solution'] and isinstance(value, str) and value:
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

    def _generate_project_messaging(self, content):
        """Generate messaging for the entire project"""
        prd = content.get('prd', {})
        strategy = content.get('strategy', {})

        # Extract key points
        project_name = prd.get('name', 'Project Alignment Tool')
        overview = self._get_clean_text(prd.get('overview', ''))
        pain_points = self._get_clean_text(prd.get('problem_statement', ''))
        solution = self._get_clean_text(prd.get('solution', ''))
        business_value = self._get_clean_text(strategy.get('business_value', ''))

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
        project_name = prd.get('name', 'Project Alignment Tool')

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
        pain_points = self._get_clean_text(prd.get('problem_statement', ''))

        if self._has_changes(changes.get('strategy', {})):
            return f"These changes refine our approach to solving the customer pain point of {pain_points[:100]}..."
        elif self._has_changes(changes.get('prd', {})):
            return f"These updates improve our solution to the customer pain point of {pain_points[:100]}..."
        else:
            return "These changes maintain our focus on addressing key customer pain points."

    def _describe_business_impact(self, content, changes):
        """Describe business impact of the changes"""
        strategy = content.get('strategy', {})
        business_value = self._get_clean_text(strategy.get('business_value', ''))

        if business_value:
            return f"These changes help us achieve {business_value[:150]}..."
        else:
            return "These changes support our business objectives and customer satisfaction goals."

    def _get_clean_text(self, text):
        """Get clean text, handling potential None values"""
        if not text:
            return ""

        # Get first sentence if possible
        clean_text = self._clean_markdown(text)
        first_sentence = re.search(r'^([^.!?]+[.!?])', clean_text)
        if first_sentence:
            return first_sentence.group(1).strip()

        # Otherwise return the whole text, truncating if needed
        if len(clean_text) > 150:
            return clean_text[:150].strip() + "..."
        return clean_text.strip()