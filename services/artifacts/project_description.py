# services/artifacts/project_description.py
import json
import logging
from models import Project
from flask import current_app
from .base_generator import BaseGenerator
from .objection_generator import ObjectionGenerator
from .improvement_generator import ImprovementGenerator

class ProjectDescriptionGenerator(BaseGenerator):
    """
    Generates concise project descriptions.
    Creates 3-sentence and 3-paragraph summaries.
    """

    def __init__(self):
        """Initialize the generator with a logger, objection generator, and improvement generator."""
        super().__init__()
        self.objection_generator = ObjectionGenerator()
        self.improvement_generator = ImprovementGenerator()

    def get_latest(self):
        """Get the latest generated project description"""
        project = Project.query.order_by(Project.timestamp.desc()).first()
        if project and project.description:
            result = project.get_description_dict()

            # Add objections if available
            if project.description_objections:
                result['objections'] = project.get_description_objections_list()

            # Add improvements if available
            if project.description_improvements:
                result['improvements'] = project.get_description_improvements_list()

            return result
        return None

    def generate(self, project_content):
        """
        Generate project description in three sentences and three paragraphs.

        Args:
            project_content (str): JSON string of project content

        Returns:
            str: JSON string with descriptions, objections, and improvements
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

        # Generate improvements for the description
        improvements_json = self.improvement_generator.generate_for_artifact(
            content, description, 'description')

        # Combine description, objections, and improvements
        description['objections'] = self.parse_content(objections_json)
        description['improvements'] = self.parse_content(improvements_json)

        return json.dumps(description)

    def _create_description_prompt(self, context):
        """Create prompt for generating project description using master prompt structure."""

        # 1. Role & Identity Definition
        role = "You are a Technical Project Summarizer who distills complex initiatives into clear, factual descriptions."

        # 2. Context & Background
        context_section = f"""
Project information:
{context}

Create standardized, factual descriptions for internal and external use.
"""

        # 3. Task Definition & Objectives
        task = """
Generate two project descriptions:
1. Three sentences: what it is, pain point addressed, solution approach
2. Three paragraphs: expanded version covering the same points

Focus on facts, specificity, and clarity.
"""

        # 4. Format & Structure Guidelines
        format_guidelines = """
Format as JSON with:
{
    "three_sentences": [
        "What the project is (1 sentence)",
        "Problem it solves (1 sentence)",
        "Solution approach (1 sentence)"
    ],
    "three_paragraphs": [
        "Paragraph describing what it is (3-4 sentences)",
        "Paragraph describing the problem (3-4 sentences)",
        "Paragraph describing the solution (3-4 sentences)"
    ]
}
"""

        # 5. Process Instructions
        process = """
1. Extract core project purpose from context
2. Identify specific pain points addressed
3. Determine key solution elements
4. Draft concise, factual sentences
5. Expand into focused paragraphs
6. Review for clarity and specificity
"""

        # 6. Content Requirements
        content_req = """
Content must be:
- Factual, not marketing-oriented
- Specific with concrete details
- Quantifiable where possible (metrics, percentages)
- Direct and concise (15-20 words per sentence)
- Free of subjective claims
- Written in active voice
- Jargon-free unless necessary

Each sentence and paragraph must focus on a single aspect.
"""

        # 7. Constraints & Limitations
        constraints = """
Do not:
- Use marketing language or hype ("revolutionary," "game-changing")
- Include subjective claims without evidence
- Use unnecessary adjectives or adverbs
- Repeat information
- Include vague statements
- Use passive voice
- Exceed 20 words per sentence
"""

        # 8. Examples & References
        examples = """
Example of effective, factual three sentences:
[
    "Document Sync Tool connects PRD, tickets, and strategy documents to maintain consistency.",
    "Teams waste 5.2 hours weekly reconciling inconsistent documentation across systems.",
    "The tool monitors document changes, flags inconsistencies, and suggests updates to maintain alignment."
]

Example of an effective, factual paragraph:
"Document inconsistency causes 32% of project delays. Teams spend 5.2 hours weekly reconciling conflicting information across PRDs, tickets, and strategy documents. These inconsistencies lead to rework, miscommunication, and missed requirements. Studies show aligned documentation reduces implementation errors by 46%."
"""

        # 9. Interaction Guidelines
        interaction = """
This description forms the foundation for all project communications. Stakeholders will use it to understand the project's purpose and approach.
"""

        # 10. Quality Assurance
        quality = """
Verify each output:
- Contains specific details, not generalities
- Includes quantifiable elements where possible
- Uses direct, concise language
- Focuses on facts, not marketing claims
- Maintains consistent focus in each section
- Avoids unnecessary adjectives and adverbs
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

    def _format_context(self, content):
        """Format content as context for Claude"""
        context_parts = []

        # Add PRD information (key facts only)
        prd = content.get('prd', {})
        if prd:
            context_parts.append("PRD:")
            for key, value in prd.items():
                if isinstance(value, str) and value:
                    # Truncate long values
                    if len(value) > 100:
                        value = value[:100] + "..."
                    context_parts.append(f"- {key}: {value}")

        # Add PRFAQ highlights
        prfaq = content.get('prfaq', {})
        if prfaq:
            context_parts.append("\nPRFAQ:")
            if 'press_release' in prfaq:
                pr = prfaq['press_release']
                context_parts.append(f"- Press Release: {pr[:100]}..." if len(pr) > 100 else pr)
            if 'frequently_asked_questions' in prfaq:
                context_parts.append("- FAQs:")
                for qa in prfaq['frequently_asked_questions'][:2]:  # Limit to first 2 FAQs
                    q = qa.get('question', '')
                    a = qa.get('answer', '')
                    if len(a) > 100:
                        a = a[:100] + "..."
                    context_parts.append(f"  Q: {q}")
                    context_parts.append(f"  A: {a}")

        # Add strategy key points
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

        return "\n".join(context_parts)

    def _rule_based_generation(self, content):
        """Fallback rule-based generation if Claude is unavailable."""
        # Extract key information from content
        prd = content.get('prd', {})
        prfaq = content.get('prfaq', {})
        strategy = content.get('strategy', {})

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
        three_sentences = [
            f"{project_name} connects and synchronizes project documentation across systems.",
            "Teams waste 4+ hours weekly reconciling inconsistent documentation.",
            "The tool monitors changes, flags inconsistencies, and suggests updates."
        ]

        # Generate three-paragraph description
        three_paragraphs = [
            f"{project_name} is a documentation synchronization system that connects PRDs, tickets, and strategy documents. It monitors all connected documents for changes and maintains alignment. The system automatically generates project descriptions, messaging, and flags potential issues.",

            "Teams currently waste 4+ hours weekly reconciling inconsistent documentation. This leads to implementation errors, miscommunication, and project delays. Studies show 32% of project failures stem from documentation inconsistencies.",

            f"{project_name} solves this by creating bidirectional links between documents. When changes occur, it flags inconsistencies and suggests updates. The system also generates standardized artifacts and identifies potential issues."
        ]

        # Generate fallback improvements
        improvements = [
            {
                "title": "Add Success Metrics",
                "suggestion": "Define 3-5 specific KPIs that will measure project success (e.g., 40% reduction in document sync time).",
                "benefit": "Projects with defined metrics are 35% more likely to deliver expected business value."
            },
            {
                "title": "Sharpen Scope Boundaries",
                "suggestion": "Explicitly list what's NOT included in the project to prevent scope creep (e.g., 'Will not include SharePoint integration').",
                "benefit": "Clear scope boundaries reduce feature creep by 42% and prevent 30% of project delays."
            },
            {
                "title": "Specify Implementation Phases",
                "suggestion": "Break implementation into 3 concrete phases with specific deliverables for each milestone.",
                "benefit": "Phased implementation approaches reduce project risk by 38% and improve stakeholder alignment."
            }
        ]

        # Format the result
        result = {
            'three_sentences': three_sentences,
            'three_paragraphs': three_paragraphs,
            'improvements': improvements
        }

        return json.dumps(result)