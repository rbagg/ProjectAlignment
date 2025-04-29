# services/artifacts/improvement_generator.py
import json
import logging
from models import Project
from .base_generator import BaseGenerator
from prompts import get_prompt

class ImprovementGenerator(BaseGenerator):
    """
    Generates positive improvement suggestions for project artifacts.
    Provides actionable ways to strengthen communication and prevent scope creep.
    """

    def get_latest(self):
        """
        Get latest improvements from database.
        Required implementation of abstract method from BaseGenerator.

        Returns:
            dict: Latest improvements or None
        """
        project = Project.query.order_by(Project.timestamp.desc()).first()
        if not project:
            return None

        return {
            'description': project.get_description_improvements_list(),
            'internal': project.get_internal_improvements_list(),
            'external': project.get_external_improvements_list()
        }

    def generate(self, project_content, artifact_type='description'):
        """
        Generate improvements for project content.
        Required implementation of abstract method from BaseGenerator.

        Args:
            project_content (str): JSON string of project content
            artifact_type (str): Type of artifact to generate improvements for

        Returns:
            str: JSON string of improvements
        """
        content = self.parse_content(project_content)

        # For this method, we'll just use generate_for_artifact
        # with a dummy artifact content since that's what we actually want to use
        dummy_artifact = {"type": artifact_type}
        return self.generate_for_artifact(content, dummy_artifact, artifact_type)

    # Enhanced approach for the ImprovementGenerator - Focus on focus, simplification and pushing boundaries

    def generate_for_artifact(self, project_content, artifact_content, artifact_type):
        """
        Generate substantive improvements focusing on focus, simplification and pushing boundaries

        Args:
            project_content (dict): The project content
            artifact_content (dict): The artifact content to improve
            artifact_type (str): Type of artifact ('description', 'internal', 'external')

        Returns:
            str: JSON string of improvement suggestions
        """
        # Format context for the improved prompt
        context = self._format_context(project_content)

        # Convert artifact content to a formatted string
        artifact_string = json.dumps(artifact_content, indent=2)

        # Create a more challenging prompt focused on focus, simplification and pushing boundaries
        prompt = f"""
        # Strategic Enhancement Challenge

        You are a Strategic Enhancement Specialist tasked with identifying ways to sharpen focus, eliminate unnecessary scope, 
        and push the boundaries of what's possible for this project. Your goal is to help create a more focused,
        impactful project by suggesting substantive strategic improvements.

        ## Project Context
        {context}

        ## Artifact to Enhance
        {artifact_string}

        ## Your Task
        Generate 3-4 substantial, thought-provoking improvements that:

        1. Sharpen focus by eliminating unnecessary effort or scope
        2. Push the limits of what's possible by challenging conventional approaches
        3. Identify the minimum version that would deliver meaningful results
        4. Suggest radical simplifications that could make the project more impactful
        5. Propose counterintuitive approaches that could lead to breakthrough results

        FORMAT:
        Provide your response as a JSON array of improvement objects with these properties:
        - "title": Brief, compelling name of the improvement (3-6 words)
        - "suggestion": Specific, actionable recommendation that challenges conventional thinking
        - "rationale": Why this approach would lead to better outcomes
        - "minimum_version": A stripped-down version of this idea that could be implemented quickly

        IMPORTANT:
        - Focus on substantial strategic improvements, not cosmetic or formatting changes
        - Do NOT suggest simply adding more detail or sections - focus on focus and impact
        - Propose ideas that might initially seem uncomfortable or challenging
        - Each improvement should push the team to think differently about the project
        - At least one suggestion should involve radical simplification or scope reduction
        """

        # Generate improvements with the improved approach
        improvements_json = self.generate_with_claude(
            prompt=prompt,
            fallback_method=self._strategic_fallback_improvements,
            fallback_args={'artifact_type': artifact_type, 'artifact_content': artifact_content}
        )

        return improvements_json

    def _strategic_fallback_improvements(self, artifact_type, artifact_content):
        """Provide strategic fallback improvements that challenge conventional thinking"""
        if artifact_type == 'description':
            return json.dumps([
                {
                    "title": "Single Source Model",
                    "suggestion": "Instead of building connectors to sync multiple documents, create a single-source model where all documents are generated views of a central data model.",
                    "rationale": "Eliminating the need to sync by having one source of truth is fundamentally more reliable than trying to keep multiple sources synchronized.",
                    "minimum_version": "Start with just PRDs and tickets sharing a common data backend, with documents generated as views from this source."
                },
                {
                    "title": "Human-In-Loop Only",
                    "suggestion": "Remove all automated update suggestions and focus solely on detecting inconsistencies, requiring human approval for all changes to ensure context and intent are preserved.",
                    "rationale": "The most challenging aspect is detecting inconsistencies, not suggesting updates. By focusing only on inconsistency detection, you dramatically simplify the ML requirements while still providing 80% of the value.",
                    "minimum_version": "A simple diff tool that highlights inconsistencies between two documents without attempting to suggest updates."
                },
                {
                    "title": "Documentation as Tests",
                    "suggestion": "Reframe documentation as executable tests that verify the software matches the documented behavior, turning documentation inconsistencies into failing tests.",
                    "rationale": "By making documentation executable, you ensure it stays accurate because failing tests immediately signal when implementation and documentation diverge.",
                    "minimum_version": "Generate basic automated tests from key requirements in the PRD that verify core functionality."
                }
            ])
        elif artifact_type == 'internal':
            return json.dumps([
                {
                    "title": "Weekly Manual Pilot",
                    "suggestion": "Before building any software, run a completely manual process for 4 weeks where a team member manually identifies inconsistencies and suggests updates via comments.",
                    "rationale": "This approach lets you validate the value proposition immediately, refine the detection criteria based on real usage, and collect training data for later automation - all without writing code.",
                    "minimum_version": "One person spending 2 hours every Friday reviewing docs and adding comments on inconsistencies."
                },
                {
                    "title": "Team-Specific MVP First",
                    "suggestion": "Instead of building for all teams and document types, focus on just one high-value team and their two most important document types for the initial release.",
                    "rationale": "A focused solution for one team lets you validate the approach, demonstrate value, and create internal advocates before expanding. It dramatically reduces initial scope while still proving the concept.",
                    "minimum_version": "Connect only the Product and Engineering teams' documents (PRDs and tickets) for a single product area."
                },
                {
                    "title": "Piggyback Existing Reviews",
                    "suggestion": "Instead of creating a new system, add inconsistency detection to existing review processes like PR reviews, design reviews, and sprint planning.",
                    "rationale": "By embedding your solution into existing processes, you eliminate the adoption hurdle of a new tool and workflow while still addressing the core problem.",
                    "minimum_version": "A simple checklist of document consistency checks added to the existing PR review template."
                }
            ])
        elif artifact_type == 'external':
            return json.dumps([
                {
                    "title": "Value-Based Pricing Model",
                    "suggestion": "Instead of subscription pricing, charge based on documented time savings or error reduction, taking a percentage of the proven value delivered.",
                    "rationale": "This aligns your incentives with customer success, eliminates adoption risk for customers, and forces you to focus on measurable outcomes rather than features.",
                    "minimum_version": "A simple time tracking feature that measures before/after time spent on documentation tasks."
                },
                {
                    "title": "Document-Free Positioning",
                    "suggestion": "Position the product as eliminating the need for traditional documents entirely rather than keeping them in sync, creating a new category instead of competing in an existing one.",
                    "rationale": "By positioning as the solution that makes traditional documents obsolete, you create a stronger, more disruptive value proposition that's harder for competitors to copy.",
                    "minimum_version": "A 'document-free' mode that represents requirements as structured data rather than traditional documents."
                },
                {
                    "title": "Customer-Sourced Examples",
                    "suggestion": "Replace all hypothetical benefits with real, specific, customer-sourced examples of documentation failures and their costs.",
                    "rationale": "Real examples are more credible and relatable than generic claims, and force you to validate your value proposition with actual customer evidence.",
                    "minimum_version": "A landing page with 3-5 specific, quantified stories of documentation failures from customer interviews."
                }
            ])
        else:
            return json.dumps([
                {
                    "title": "Ruthless MVP Definition",
                    "suggestion": "Define the absolute minimum product that delivers value by cutting the scope to just one document type, one connector, and manual approval of all changes.",
                    "rationale": "By dramatically reducing initial scope, you can launch sooner, validate assumptions faster, and iterate based on real usage data instead of speculation.",
                    "minimum_version": "A simple tool that just identifies inconsistencies between PRDs and tickets, with no automated updates."
                },
                {
                    "title": "Opposite Approach Test",
                    "suggestion": "Instead of building technology to keep documents in sync, test creating a small, dedicated team of 'documentation synchronizers' who manually ensure alignment.",
                    "rationale": "Starting with a manual service lets you deeply understand the problem space before committing to a technical approach, while still delivering immediate value to customers.",
                    "minimum_version": "A 4-week experiment with one person manually synchronizing documents for a single team."
                },
                {
                    "title": "Radical Transparency Design",
                    "suggestion": "Design the system to publicly display and quantify documentation inconsistencies across teams, creating social pressure to maintain alignment.",
                    "rationale": "Making inconsistencies visible creates natural incentives for teams to fix them, potentially eliminating the need for complex automation of updates.",
                    "minimum_version": "A simple dashboard showing 'documentation health scores' for each team based on consistency metrics."
                }
            ])

    def _format_context(self, content):
        """Format content as context for Claude"""
        if isinstance(content, str):
            content = self.parse_content(content)

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
                context_parts.append(f"- FAQs: {len(prfaq['frequently_asked_questions'])} questions")

        # Add strategy key points
        strategy = content.get('strategy', {})
        if strategy:
            context_parts.append("\nStrategy:")
            for key, value in strategy.items():
                if isinstance(value, str) and value:
                    if len(value) > 100:
                        value = value[:100] + "..."
                    context_parts.append(f"- {key}: {value}")

        # Add ticket count only
        tickets = content.get('tickets', [])
        if tickets:
            context_parts.append(f"\nTickets: {len(tickets)} total")

        return "\n".join(context_parts)

    def _fallback_improvements(self, artifact_type):
        """Provide fallback improvements if Claude fails."""
        if artifact_type == 'description':
            return json.dumps([
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
            ])
        elif artifact_type == 'internal':
            return json.dumps([
                {
                    "title": "Add RACI Matrix",
                    "suggestion": "Include a simple RACI chart showing team responsibilities for key deliverables.",
                    "benefit": "Clear responsibility assignment reduces delivery delays by 28% and eliminates redundant work."
                },
                {
                    "title": "Prioritize Implementation Tasks",
                    "suggestion": "Categorize implementation tasks as P0 (critical), P1 (important), and P2 (nice-to-have).",
                    "benefit": "Prioritized task lists improve team focus by 32% and increase on-time delivery rates."
                },
                {
                    "title": "Add Dependency Timeline",
                    "suggestion": "Create a visual timeline showing cross-team dependencies and delivery dates.",
                    "benefit": "Dependency timelines reduce blocking issues by 45% and improve cross-team coordination."
                }
            ])
        elif artifact_type == 'external':
            return json.dumps([
                {
                    "title": "Add Customer Testimonial",
                    "suggestion": "Include a brief quote from a beta customer with specific results achieved.",
                    "benefit": "Customer testimonials increase conversion rates by 34% and build credibility."
                },
                {
                    "title": "Create Comparison Table",
                    "suggestion": "Add a simple 3-column table comparing your solution vs. alternatives vs. doing nothing.",
                    "benefit": "Direct comparison tables improve conversion by 28% by addressing alternative evaluation directly."
                },
                {
                    "title": "Add ROI Calculator Link",
                    "suggestion": "Include a link to a simple calculator where prospects can estimate their specific ROI.",
                    "benefit": "Interactive ROI tools increase qualified leads by 40% and decrease sales cycle length."
                }
            ])
        else:
            return json.dumps([
                {
                    "title": "Add Specific Examples",
                    "suggestion": "Include 2-3 concrete examples that illustrate key points.",
                    "benefit": "Specific examples improve comprehension by 42% and increase message retention."
                }
            ])

    def _generate_description_improvements(self, project_content, description):
        """Generate improvements for the project description."""
        context = self._format_context(project_content)

        # Convert artifact content to a formatted string
        artifact_string = json.dumps(description, indent=2)

        # Get improvement generator prompt from centralized prompt system
        prompt = get_prompt('improvement_generator', context, artifact=artifact_string, artifact_type='description')

        return self.generate_with_claude(
            prompt=prompt,
            fallback_method=self._fallback_improvements,
            fallback_args={'artifact_type': 'description'}
        )

    def _generate_internal_improvements(self, project_content, messaging):
        """Generate improvements for the internal messaging."""
        context = self._format_context(project_content)

        # Convert artifact content to a formatted string
        artifact_string = json.dumps(messaging, indent=2)

        # Get improvement generator prompt from centralized prompt system
        prompt = get_prompt('improvement_generator', context, artifact=artifact_string, artifact_type='internal')

        return self.generate_with_claude(
            prompt=prompt,
            fallback_method=self._fallback_improvements,
            fallback_args={'artifact_type': 'internal'}
        )

    def _generate_external_improvements(self, project_content, messaging):
        """Generate improvements for the external messaging."""
        context = self._format_context(project_content)

        # Convert artifact content to a formatted string
        artifact_string = json.dumps(messaging, indent=2)

        # Get improvement generator prompt from centralized prompt system
        prompt = get_prompt('improvement_generator', context, artifact=artifact_string, artifact_type='external')

        return self.generate_with_claude(
            prompt=prompt,
            fallback_method=self._fallback_improvements,
            fallback_args={'artifact_type': 'external'}
        )