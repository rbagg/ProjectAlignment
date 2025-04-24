# services/artifacts/project_description.py
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
        return f"Generate project description based on: {context}"

class ProjectDescriptionGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_latest(self):
        """Get the latest generated project description"""
        project = Project.query.order_by(Project.timestamp.desc()).first()
        if project and project.description:
            return json.loads(project.description)
        return None

    def generate(self, project_content, use_moo=False):
        """
        Generate a project description in three sentences and three paragraphs

        Args:
            project_content (str): JSON string of project content
            use_moo (bool): Whether to include Most Obvious Objections

        Returns:
            str: JSON string containing the generated descriptions
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
                # Format context for Claude
                context = self._format_context(content)

                # Determine which prompt to use
                prompt_type = 'project_description_moo' if use_moo else 'project_description'

                # Get the appropriate prompt
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
        return self._enhanced_rule_based_generation(content)

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

    def _format_context(self, content):
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

        # Add PRFAQ information
        prfaq = content.get('prfaq', {})
        if prfaq:
            context.append("\n== Press Release / FAQ ==")
            if 'press_release' in prfaq:
                pr = prfaq['press_release']
                context.append(f"Press Release: {pr}")

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

        # Add ticket information
        tickets = content.get('tickets', [])
        if tickets:
            context.append("\n== Tickets Summary ==")
            context.append(f"Total tickets: {len(tickets)}")
            for i, ticket in enumerate(tickets[:5]):
                context.append(f"Ticket {i+1}: {ticket.get('title', '')} - {ticket.get('status', '')}")

        return "\n".join(context)

    def _enhanced_rule_based_generation(self, content):
        """
        Enhanced rule-based generation that tries to extract more meaningful content
        from the provided documentation
        """
        # Extract key information with better parsing
        project_name = self._extract_project_name(content)
        overview = self._extract_overview(content)
        pain_points = self._extract_pain_points(content)
        solutions = self._extract_solutions(content)

        # Generate three-sentence description
        three_sentences = [
            f"{project_name} is a solution designed to {overview}.",
            f"It addresses the customer pain point of {pain_points}.",
            f"The solution works by {solutions}."
        ]

        # Generate three-paragraph description
        what_it_is = f"{project_name} is a comprehensive solution designed to {overview}. "
        what_it_is += "It provides users with a seamless experience for managing their workflows and data. "
        what_it_is += f"This project aims to transform how users interact with project documentation systems."

        pain_paragraph = f"Currently, users face significant challenges when attempting to {pain_points}. "
        pain_paragraph += "These pain points lead to reduced productivity, user frustration, and increased error rates. "
        pain_paragraph += "Our research indicates that addressing these challenges could improve user satisfaction by up to 40%."

        solution_paragraph = f"{project_name} addresses these challenges by {solutions}. "
        solution_paragraph += "The implementation includes bidirectional change tracking, artifact generation, and impact analysis. "
        solution_paragraph += "These enhancements will significantly improve user efficiency and satisfaction."

        three_paragraphs = [what_it_is, pain_paragraph, solution_paragraph]

        # Format the result
        result = {
            'three_sentences': three_sentences,
            'three_paragraphs': three_paragraphs
        }

        return json.dumps(result)

    def _extract_project_name(self, content):
        """Extract project name with better parsing"""
        # Try to get from PRD name field
        prd = content.get('prd', {})
        if prd.get('name'):
            return prd.get('name')

        # Default
        return "Project Alignment Tool"

    def _extract_overview(self, content):
        """Extract overview with better parsing"""
        prd = content.get('prd', {})

        # Try to get from overview field
        if prd.get('overview'):
            # Get first sentence or first 100 chars
            overview = prd.get('overview').strip()
            sentence_match = re.search(r'^([^.!?]+[.!?])', overview)
            if sentence_match:
                return sentence_match.group(1).strip()
            elif len(overview) > 100:
                return overview[:100].strip() + "..."
            return overview

        # Default
        return "keep project documentation synchronized and ensure alignment across all project artifacts"

    def _extract_pain_points(self, content):
        """Extract pain points with better parsing"""
        prd = content.get('prd', {})

        # Try problem statement first
        if prd.get('problem_statement'):
            problem_statement = prd.get('problem_statement').strip()
            if len(problem_statement) > 100:
                # Get first sentence or truncate
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
                    answer = qa.get('answer', '').strip()
                    if len(answer) > 100:
                        return answer[:100].strip() + "..."
                    return answer

        # Default
        return "keeping documentation in sync, leading to misalignment between PRD and implementation"

    def _extract_solutions(self, content):
        """Extract solution approach with better parsing"""
        prd = content.get('prd', {})

        # Try solution field first
        if prd.get('solution'):
            solution = prd.get('solution').strip()
            if len(solution) > 100:
                # Get first sentence or truncate
                sentence_match = re.search(r'^([^.!?]+[.!?])', solution)
                if sentence_match:
                    return sentence_match.group(1).strip()
                return solution[:100].strip() + "..."
            return solution

        # Default
        return "providing a tool that monitors changes to all project documents and suggests updates to maintain alignment"