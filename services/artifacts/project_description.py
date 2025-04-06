# services/artifacts/project_description.py
import json
import logging
from models import Project
from flask import current_app
import anthropic

class ProjectDescriptionGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_latest(self):
        """Get the latest generated project description"""
        project = Project.query.order_by(Project.timestamp.desc()).first()
        if project and project.description:
            return json.loads(project.description)
        return None

    def generate(self, project_content):
        """
        Generate a project description in three sentences and three paragraphs using Claude

        Args:
            project_content (str): JSON string of project content

        Returns:
            str: JSON string containing the generated descriptions
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
            return self._rule_based_generation(content)

        # Format content for Claude
        context = self._format_context(content)

        # Create prompt for Claude
        prompt = f"""
        I need to create concise descriptions for a project based on the following information:

        {context}

        Please generate:
        1. Three sentences that describe what the project is, the customer pain point it's solving, and how it's being addressed.
        2. Three paragraphs that expand on these same points.

        Format the response as JSON with the following structure:
        {{
            "three_sentences": ["Sentence 1", "Sentence 2", "Sentence 3"],
            "three_paragraphs": ["Paragraph 1", "Paragraph 2", "Paragraph 3"]
        }}

        Make sure each sentence and paragraph focuses on one of the three key aspects (what it is, pain point, solution).
        """

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
                return self._rule_based_generation(content)

        except Exception as e:
            self.logger.error(f"Error generating project description with Claude: {str(e)}")
            # Fall back to rule-based generation
            return self._rule_based_generation(content)

    def _format_context(self, content):
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

    def _rule_based_generation(self, content):
        """Fallback rule-based generation if Claude is unavailable"""
        # Extract key information from content
        prd = content.get('prd', {})
        prfaq = content.get('prfaq', {})
        strategy = content.get('strategy', {})
        tickets = content.get('tickets', [])

        # Extract project name and overview
        project_name = prd.get('name', 'Project')
        overview = prd.get('overview', '')

        # Extract customer pain points
        pain_points = []
        if 'problem_statement' in prd:
            pain_points.append(prd['problem_statement'])
        if 'customer_pain_points' in prd:
            pain_points.extend(prd['customer_pain_points'])
        if 'frequently_asked_questions' in prfaq:
            for qa in prfaq['frequently_asked_questions']:
                if 'problem' in qa.get('question', '').lower():
                    pain_points.append(qa.get('answer', ''))

        # Extract solution approach
        solutions = []
        if 'solution' in prd:
            solutions.append(prd['solution'])
        if 'approach' in strategy:
            solutions.append(strategy['approach'])

        # Generate three-sentence description
        three_sentences = self._generate_three_sentences(
            project_name, overview, pain_points, solutions)

        # Generate three-paragraph description
        three_paragraphs = self._generate_three_paragraphs(
            project_name, overview, pain_points, solutions, tickets)

        # Format the result
        result = {
            'three_sentences': three_sentences,
            'three_paragraphs': three_paragraphs
        }

        return json.dumps(result)

    def _generate_three_sentences(self, project_name, overview, pain_points, solutions):
        """Generate a three-sentence description of the project"""
        # Sentence 1: What it is
        what_it_is = f"{project_name} is a solution designed to {overview[:100]}..."

        # Sentence 2: Pain point
        pain_point = "It addresses the customer pain point of "
        if pain_points:
            pain_point += pain_points[0][:100] + "..."
        else:
            pain_point += "improving user experience and workflow efficiency."

        # Sentence 3: Solution approach
        solution = "The solution works by "
        if solutions:
            solution += solutions[0][:100] + "..."
        else:
            solution += "providing an intuitive interface and streamlined process flow."

        return [what_it_is, pain_point, solution]

    def _generate_three_paragraphs(self, project_name, overview, pain_points, solutions, tickets):
        """Generate a three-paragraph description of the project"""
        # Paragraph 1: What it is (expanded)
        what_it_is = f"{project_name} is a comprehensive solution designed to {overview}. "
        what_it_is += "It provides users with a seamless experience for managing their workflows and data. "
        what_it_is += f"This project aims to transform how users interact with {project_name.lower()} systems."

        # Paragraph 2: Pain point (expanded)
        pain_point = "Currently, users face significant challenges when attempting to "
        if pain_points:
            pain_point += ", ".join(p[:50] + "..." for p in pain_points[:2])
        else:
            pain_point += "complete their tasks efficiently and accurately."
        pain_point += " These pain points lead to reduced productivity, user frustration, and increased error rates. "
        pain_point += "Our research indicates that addressing these challenges could improve user satisfaction by up to 40%."

        # Paragraph 3: Solution approach (expanded)
        solution = f"{project_name} addresses these challenges by "
        if solutions:
            solution += ", ".join(s[:50] + "..." for s in solutions[:2])
        else:
            solution += "providing an intuitive user interface and streamlined workflow."
        solution += " The implementation includes "
        if tickets:
            features = [t.get('title', '').split(':')[-1].strip() for t in tickets[:3]]
            solution += ", ".join(features)
        else:
            solution += "key features and improvements to the current system"
        solution += ". These enhancements will significantly improve user efficiency and satisfaction."

        return [what_it_is, pain_point, solution]