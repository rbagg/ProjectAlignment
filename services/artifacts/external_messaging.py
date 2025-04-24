# services/artifacts/external_messaging.py
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
        return f"Generate external messaging based on: {context}"

class ExternalMessagingGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_latest(self):
        """Get the latest generated external messaging"""
        project = Project.query.order_by(Project.timestamp.desc()).first()
        if project and project.external_messaging:
            return json.loads(project.external_messaging)
        return None

    def generate(self, project_content, changes=None, use_moo=False):
        """
        Generate external messaging for the project or changes

        Args:
            project_content (str): JSON string of project content
            changes (dict, optional): Changes detected in the project
            use_moo (bool): Whether to include Most Obvious Objections

        Returns:
            str: JSON string containing the generated external messaging
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
                    prompt_type = 'external_changes_moo' if use_moo else 'external_changes'
                    prompt = get_prompt(prompt_type, context, changes=json.dumps(changes, indent=2))
                else:
                    prompt_type = 'external_messaging_moo' if use_moo else 'external_messaging'
                    prompt = get_prompt(prompt_type, context)

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

        # Fall back to enhanced rule-based generation
        if not changes:
            return self._enhanced_generate_project_messaging(content)
        else:
            return self._enhanced_generate_change_messaging(content, changes)

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

        # Add PRFAQ information - good source for customer-focused messaging
        prfaq = content.get('prfaq', {})
        if prfaq:
            context.append("\n== Press Release / FAQ ==")
            if 'press_release' in prfaq:
                pr = prfaq['press_release']
                context.append(f"Press Release: {pr}")

            if 'frequently_asked_questions' in prfaq:
                context.append("FAQs:")
                for qa in prfaq['frequently_asked_questions']:
                    question = qa.get('question', '')
                    answer = qa.get('answer', '')
                    # Prioritize customer benefit questions
                    if any(word in question.lower() for word in ['benefit', 'value', 'help', 'solve']):
                        context.append(f"Q: {question}")
                        context.append(f"A: {answer}")

        # Add changes information
        if changes:
            context.append("\n== Recent Changes ==")
            # For external messaging, focus on customer-facing changes
            prd_changes = changes.get('prd', {})
            if prd_changes:
                if prd_changes.get('added'):
                    context.append(f"New Features: {', '.join(prd_changes['added'])}")
                if prd_changes.get('modified'):
                    context.append(f"Improved Features: {', '.join(prd_changes['modified'])}")
                if prd_changes.get('removed'):
                    context.append(f"Removed Features: {', '.join(prd_changes['removed'])}")

        return "\n".join(context)

    def _enhanced_generate_project_messaging(self, content):
        """Generate enhanced messaging for the entire project"""
        # Extract information with better parsing
        project_name = self._extract_project_name(content)
        pain_points = self._extract_pain_points(content)
        solution = self._extract_solution(content)
        benefits = self._extract_benefits(content)

        # Format the messaging
        messaging = {
            'headline': f"Introducing {project_name}",
            'pain_point': f"We know you've been struggling with {pain_points}",
            'solution': f"That's why we built {project_name}, which {solution}",
            'benefits': benefits,
            'call_to_action': f"Try {project_name} today and streamline your workflow."
        }

        return json.dumps(messaging)

    def _enhanced_generate_change_messaging(self, content, changes):
        """Generate enhanced messaging for project changes"""
        # Extract information with better parsing
        project_name = self._extract_project_name(content)
        pain_points = self._extract_pain_points(content)
        solution = self._extract_solution(content)

        # Determine if this is a new feature or an update
        is_new_feature = False
        feature_name = ""

        if self._has_changes(changes.get('prd', {})):
            if changes['prd'].get('added'):
                is_new_feature = True
                feature_name = changes['prd']['added'][0].replace('_', ' ').title()

        # Generate appropriate headline
        if is_new_feature:
            headline = f"New in {project_name}: {feature_name}"
        else:
            headline = f"{project_name} Update: Improved Experience"

        # Format the messaging
        messaging = {
            'headline': headline,
            'pain_point': f"We heard your feedback about {pain_points}",
            'solution': f"We've updated {project_name} to {solution}",
            'benefits': "This update will help you work more efficiently and reduce errors.",
            'call_to_action': f"Update now and see the difference."
        }

        return json.dumps(messaging)

    def _extract_project_name(self, content):
        """Extract project name with better parsing"""
        # Try to get from PRD name field
        prd = content.get('prd', {})
        if prd.get('name'):
            return prd.get('name')

        # Default
        return "Project Alignment Tool"

    def _extract_pain_points(self, content):
        """Extract pain points with better parsing"""
        prd = content.get('prd', {})

        # Try problem statement first
        if prd.get('problem_statement'):
            problem_statement = prd.get('problem_statement').strip()
            # Get first sentence or truncate
            if len(problem_statement) > 100:
                sentence_match = re.search(r'^([^.!?]+[.!?])', problem_statement)
                if sentence_match:
                    return sentence_match.group(1).strip()
                return problem_statement[:100].strip() + "..."
            return problem_statement

        # Check PRFAQ
        prfaq = content.get('prfaq', {})
        if prfaq.get('frequently_asked_questions'):
            for qa in prfaq.get('frequently_asked_questions'):
                if 'problem' in qa.get('question', '').lower():
                    answer = qa.get('answer', '')
                    if answer:
                        if len(answer) > 100:
                            return answer[:100].strip() + "..."
                        return answer.strip()

        # Default
        return "keeping documentation in sync, which leads to miscommunication and implementation errors"

    def _extract_solution(self, content):
        """Extract solution approach with better parsing"""
        prd = content.get('prd', {})

        # Try solution field first
        if prd.get('solution'):
            solution = prd.get('solution').strip()
            # Get first sentence or truncate
            if len(solution) > 100:
                sentence_match = re.search(r'^([^.!?]+[.!?])', solution)
                if sentence_match:
                    return sentence_match.group(1).strip()
                return solution[:100].strip() + "..."
            return solution

        # Default
        return "automatically detects changes and keeps all your project documentation in sync"

    def _extract_benefits(self, content):
        """Extract benefits with better parsing"""
        # Check PRFAQ for benefits
        prfaq = content.get('prfaq', {})
        if prfaq.get('frequently_asked_questions'):
            for qa in prfaq.get('frequently_asked_questions'):
                if any(word in qa.get('question', '').lower() for word in ['benefit', 'advantage', 'value']):
                    answer = qa.get('answer', '')
                    if answer:
                        return "This will help you " + answer[:100].strip()

        # Check strategy for business value
        strategy = content.get('strategy', {})
        if strategy.get('business_value'):
            # Adapt business value to customer perspective
            business_value = strategy.get('business_value').strip()
            customer_value = business_value.replace('our', 'your').replace('we', 'you').replace('us', 'you')
            return "This will help you " + customer_value[:100].strip()

        # Default
        return "This will help you save time and reduce errors by ensuring your team is always working from up-to-date documentation"

    def _has_changes(self, doc_changes):
        """Check if a document has any changes"""
        return (
            len(doc_changes.get('added', [])) > 0 or 
            len(doc_changes.get('modified', [])) > 0 or 
            len(doc_changes.get('removed', [])) > 0
        )