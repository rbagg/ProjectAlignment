# services/artifacts/project_description.py
import json
import logging
from models import Project
from flask import current_app
from .base_generator import BaseGenerator
from .objection_generator import ObjectionGenerator

class ProjectDescriptionGenerator(BaseGenerator):
    """
    Generator for project descriptions in three sentences and three paragraphs.

    This service creates concise descriptions of what the project is, the customer
    pain point it's solving, and how it's being addressed, along with objections
    to challenge the user's thinking.
    """

    def __init__(self):
        """Initialize the generator with a logger and objection generator."""
        super().__init__()
        self.objection_generator = ObjectionGenerator()

    def get_latest(self):
        """Get the latest generated project description"""
        project = Project.query.order_by(Project.timestamp.desc()).first()
        if project and project.description:
            result = project.get_description_dict()

            # Add objections if available
            if project.description_objections:
                result['objections'] = project.get_description_objections_list()

            return result
        return None

    def generate(self, project_content):
        """
        Generate a project description in three sentences and three paragraphs using Claude

        Args:
            project_content (str): JSON string of project content

        Returns:
            str: JSON string containing the generated descriptions
        """
        content = self.parse_content(project_content)

        # Format the context
        context = self._format_context(content)

        # Create prompt for Claude using master prompt structure
        prompt = self._create_description_prompt(context)

        # Generate description
        description_json = self.generate_with_claude(
            prompt=prompt,
            fallback_method=self._rule_based_generation,
            fallback_args={'content': content}
        )

        # Parse the description
        description = self.parse_content(description_json)

        # Generate objections for the description
        objections_json = self.objection_generator.generate_for_artifact(
            content, description, 'description')

        # Combine description and objections
        description['objections'] = self.parse_content(objections_json)

        return json.dumps(description)

    def _create_description_prompt(self, context):
        """Create prompt for generating project description using master prompt structure."""

        # 1. Role & Identity Definition
        role = "You are a Project Communications Specialist with expertise in distilling complex initiatives into clear, concise descriptions. You excel at identifying core elements of projects and communicating them in both brief and detailed formats suitable for various stakeholders."

        # 2. Context & Background
        context_section = f"""
I need to create standardized descriptions for a project based on the following information:

{context}

These descriptions will be used to ensure all stakeholders have a consistent understanding of what the project is, what problem it's solving, and how the solution works.
"""

        # 3. Task Definition & Objectives
        task = """
Your task is to generate two versions of the project description:
1. A concise three-sentence description covering what the project is, the customer pain point it's solving, and how it's being addressed
2. An expanded three-paragraph description that elaborates on these same three points

Each version must capture the essence of the project while being clear and accessible to both technical and non-technical audiences.
"""

        # 4. Format & Structure Guidelines
        format_guidelines = """
Structure your response as JSON with the following format:
{
    "three_sentences": [
        "Sentence describing what the project is",
        "Sentence describing the customer pain point",
        "Sentence describing how the solution addresses the pain point"
    ],
    "three_paragraphs": [
        "Paragraph elaborating on what the project is (3-5 sentences)",
        "Paragraph elaborating on the customer pain point (3-5 sentences)",
        "Paragraph elaborating on the solution approach (3-5 sentences)"
    ]
}

Each sentence in the three-sentence version should be focused on a single aspect (what, why, how).
Each paragraph in the three-paragraph version should expand on one of these aspects with supporting details.
"""

        # 5. Process Instructions
        process = """
Follow these steps to create effective project descriptions:
1. Review all provided information to identify the project's core purpose
2. Identify the specific customer pain point being addressed
3. Extract the key elements of the solution approach
4. Draft three focused sentences, each addressing one aspect
5. Expand each sentence into a cohesive paragraph with supporting details
6. Review for clarity, accuracy, and consistency between the versions
"""

        # 6. Content Requirements
        content_req = """
The descriptions must include:
- The project's primary function and scope
- Specific customer pain points or problems being solved
- The core approach or methodology used to address the problem
- Concrete benefits or outcomes expected
- Technical accuracy while remaining accessible

The language should be:
- Clear and concise without unnecessary jargon
- Specific rather than generic
- Active rather than passive
- Balanced between technical accuracy and accessibility
"""

        # 7. Constraints & Limitations
        constraints = """
Avoid:
- Marketing hyperbole or exaggerated claims
- Technical implementation details unnecessary for understanding the concept
- Vague or generic descriptions that could apply to any project
- Focusing on features without connecting them to benefits
- Introducing scope or elements not supported by the provided information
"""

        # 8. Examples & References
        examples = """
Example of a good three-sentence description:
[
    "Project Clarity is a document automation system that standardizes and connects all project documentation across departments.",
    "Teams currently struggle with inconsistent documentation formats and manual updates, leading to misalignment and duplicated effort.",
    "The solution provides intelligent templates, real-time synchronization, and automated change notifications to maintain alignment with minimal manual effort."
]

Example of a good paragraph (expanding on the pain point):
"Currently, teams waste an average of 12 hours per week dealing with documentation inconsistencies across departments. Product requirements, technical specifications, and customer-facing materials often contain conflicting information, leading to implementation errors and rework. When changes occur, updates must be manually propagated across all documents, a process that is error-prone and often overlooked during time-sensitive releases. This results in downstream teams working from outdated information and creates significant alignment issues that impact product quality and customer satisfaction."
"""

        # 9. Interaction Guidelines
        interaction = """
This description will serve as a foundation for project communications. It should be designed to stand alone without requiring additional explanation, as it will be referenced by stakeholders who may not have been involved in its creation.
"""

        # 10. Quality Assurance
        quality = """
Before finalizing your descriptions, verify that:
- Both versions accurately reflect the same core information
- All three aspects (what, why, how) are clearly addressed
- The descriptions are specific to this project, not generic
- Technical accuracy is maintained while remaining accessible
- The language is clear, concise, and free of unnecessary jargon
- There is a logical flow between sentences and paragraphs
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

        # Generate fallback objections
        objections = [
            {
                "title": "Unclear Problem Definition",
                "explanation": "The description doesn't clearly quantify the problem's impact or provide evidence that it's a significant issue worth solving."
            },
            {
                "title": "Alternative Solutions Not Addressed",
                "explanation": "The description doesn't explain why this particular solution approach was chosen over alternatives."
            },
            {
                "title": "Implementation Challenges Understated",
                "explanation": "The description minimizes potential implementation challenges, particularly around integration with existing systems and processes."
            }
        ]

        # Format the result
        result = {
            'three_sentences': three_sentences,
            'three_paragraphs': three_paragraphs,
            'objections': objections
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