# services/artifacts/external_messaging.py
import json
import logging
from models import Project
from flask import current_app
from .base_generator import BaseGenerator
from .objection_generator import ObjectionGenerator

class ExternalMessagingGenerator(BaseGenerator):
    """
    Generates external customer-facing messaging.
    Creates concise, factual value propositions and calls to action.
    """

    def __init__(self):
        """Initialize the generator with a logger and objection generator."""
        super().__init__()
        self.objection_generator = ObjectionGenerator()

    def get_latest(self):
        """Get the latest generated external messaging"""
        project = Project.query.order_by(Project.timestamp.desc()).first()
        if project and project.external_messaging:
            result = project.get_external_messaging_dict()

            # Add objections if available
            if project.external_objections:
                result['objections'] = project.get_external_objections_list()

            return result
        return None

    def generate(self, project_content, changes=None):
        """
        Generate external messaging for the project or changes.

        Args:
            project_content (str): JSON string of project content
            changes (dict, optional): Changes detected in the project

        Returns:
            str: JSON string containing the generated external messaging
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
            content, messaging, 'external')

        # Combine messaging and objections
        messaging['objections'] = self.parse_content(objections_json)

        return json.dumps(messaging)

    def _create_project_prompt(self, context):
        """Create prompt for generating messaging for the entire project"""

        # 1. Role & Identity Definition
        role = "You are a Technical Product Communicator who creates factual, direct customer messaging."

        # 2. Context & Background
        context_section = f"""
Project information:
{context}

Create external customer-facing messaging that clearly communicates value.
"""

        # 3. Task Definition & Objectives
        task = """
Generate customer messaging with:
1. A direct headline focused on a key benefit
2. A clear statement of the customer problem
3. A factual explanation of the solution
4. Specific benefits with quantifiable impact
5. A straightforward call to action

Focus on clarity, specificity, and factual information.
"""

        # 4. Format & Structure Guidelines
        format_guidelines = """
Format as JSON with:
{
    "headline": "Direct statement of primary benefit (5-9 words)",
    "pain_point": "Customer problem statement (1-2 sentences)",
    "solution": "How the product solves this (1-2 sentences)",
    "benefits": "3 specific benefits with metrics when possible (1-2 sentences)",
    "call_to_action": "Clear next step (1 sentence)"
}
"""

        # 5. Process Instructions
        process = """
1. Identify the core customer problem
2. Extract key solution capabilities
3. Determine measurable benefits
4. Draft direct, factual statements for each section
5. Focus on specificity and quantifiable elements
6. Eliminate marketing language and hyperbole
7. Review for clarity, directness, and factual accuracy
"""

        # 6. Content Requirements
        content_req = """
Content must be:
- Factual with specific details
- Quantifiable where possible (numbers, percentages)
- Direct and concise (under 20 words per sentence)
- Free of subjective claims
- Written in active voice
- Jargon-free unless necessary
- Benefit-focused rather than feature-focused

The headline must state a clear benefit.
The pain point must be a problem customers recognize.
The solution must directly address the stated pain point.
Benefits must be specific and ideally measurable.
Call to action must be clear and actionable.
"""

        # 7. Constraints & Limitations
        constraints = """
Do not:
- Use marketing language or hype ("revolutionary," "game-changing")
- Make subjective claims without evidence
- Use unnecessary adjectives or adverbs
- Include vague or generic statements
- Use passive voice
- Exceed 20 words per sentence
- Focus on features without connecting to benefits
"""

        # 8. Examples & References
        examples = """
Example of effective, factual messaging:

{
    "headline": "Cut documentation time by 62%",
    "pain_point": "Your team wastes 4+ hours weekly reconciling inconsistent documentation across systems. This leads to implementation errors, miscommunication, and project delays.",
    "solution": "Our tool monitors all connected documents for changes and automatically flags inconsistencies. It suggests specific updates to maintain alignment across PRDs, tickets, and strategy documents.",
    "benefits": "Reduce documentation busywork by 62%. Decrease implementation errors by 45%. Improve cross-team alignment with 85% fewer documentation-related questions.",
    "call_to_action": "Start a 14-day trial with your actual documents to measure time savings."
}
"""

        # 9. Interaction Guidelines
        interaction = """
This messaging will be used in customer communications where factual clarity is essential for building trust and setting accurate expectations.
"""

        # 10. Quality Assurance
        quality = """
Verify the output:
- Contains specific details, not generalities
- Includes quantifiable elements where possible
- Uses direct, concise language
- Focuses on facts, not marketing claims
- Benefits are specific and ideally measurable
- Free of hype or exaggeration
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
        role = "You are a Technical Product Update Communicator who creates factual, direct customer messaging about product changes."

        # 2. Context & Background
        context_section = f"""
Project information and changes:
{context}

Create external messaging about these product updates for customers.
"""

        # 3. Task Definition & Objectives
        task = """
Generate update messaging with:
1. A direct headline stating the key improvement
2. A brief reminder of the problem being solved
3. Specific details about what changed and why it matters
4. A clear call to action

Focus on practical improvements and factual value.
"""

        # 4. Format & Structure Guidelines
        format_guidelines = """
Format as JSON with:
{
    "headline": "Direct statement of update benefit (5-9 words)",
    "pain_point": "Brief reminder of the problem (1 sentence)",
    "solution": "What changed and why it matters (2-3 sentences)",
    "call_to_action": "Clear next step (1 sentence)"
}
"""

        # 5. Process Instructions
        process = """
1. Identify the key improvements in the updates
2. Extract measurable customer benefits from these changes
3. Draft direct, factual statements about what changed
4. Focus on specificity and quantifiable improvements
5. Eliminate marketing language and hyperbole
6. Review for clarity, directness, and factual accuracy
"""

        # 6. Content Requirements
        content_req = """
Content must be:
- Factual with specific details about the changes
- Quantifiable where possible (numbers, percentages)
- Direct and concise (under 20 words per sentence)
- Free of subjective claims
- Written in active voice
- Jargon-free unless necessary
- Focused on practical customer benefits

The headline must state a clear benefit from the update.
The pain point must briefly remind customers of the problem.
The solution must explain what changed and why it matters.
Call to action must be relevant to existing customers.
"""

        # 7. Constraints & Limitations
        constraints = """
Do not:
- Use marketing language or hype ("revolutionary," "game-changing")
- Make subjective claims without evidence
- Use unnecessary adjectives or adverbs
- Include vague statements about "improvements" without specifics
- Use passive voice
- Exceed 20 words per sentence
- Focus on changes without explaining customer benefit
"""

        # 8. Examples & References
        examples = """
Example of effective, factual update messaging:

{
    "headline": "Export data 3x faster",
    "pain_point": "Large data exports previously took too long for time-sensitive analysis.",
    "solution": "We've rebuilt the export engine to process data 3x faster. This update also adds CSV and Excel export options, and lets you schedule automatic exports on a daily or weekly basis.",
    "call_to_action": "Try the new export options in your dashboard today."
}
"""

        # 9. Interaction Guidelines
        interaction = """
This messaging will be sent to existing customers who want to know what changed and how it benefits them specifically.
"""

        # 10. Quality Assurance
        quality = """
Verify the output:
- Clearly explains what actually changed
- Connects changes to specific customer benefits
- Uses direct, concise language
- Focuses on facts, not marketing claims
- Free of hype or exaggeration
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

        # Add PRFAQ highlights
        prfaq = content.get('prfaq', {})
        if prfaq:
            context_parts.append("\nPRFAQ:")
            if 'press_release' in prfaq:
                pr = prfaq['press_release']
                context_parts.append(f"- Press Release: {pr[:100]}..." if len(pr) > 100 else pr)
            if 'frequently_asked_questions' in prfaq:
                context_parts.append("- FAQs:")
                for qa in prfaq['frequently_asked_questions'][:2]:
                    q = qa.get('question', '')
                    a = qa.get('answer', '')
                    if len(a) > 100:
                        a = a[:100] + "..."
                    context_parts.append(f"  Q: {q}")
                    context_parts.append(f"  A: {a}")

        # Add changes information if provided
        if changes:
            context_parts.append("\nChanges:")
            for doc_type, doc_changes in changes.items():
                if doc_type == 'prd':
                    context_parts.append("- Product changes:")
                    if doc_changes.get('added'):
                        context_parts.append(f"  Added: {', '.join(doc_changes['added'])}")
                    if doc_changes.get('modified'):
                        context_parts.append(f"  Modified: {', '.join(doc_changes['modified'])}")

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
            'headline': f"Cut documentation time by 62%",
            'pain_point': "Your team wastes 4+ hours weekly reconciling inconsistent documentation across systems. This leads to implementation errors and project delays.",
            'solution': f"{project_name} monitors all connected documents for changes and automatically flags inconsistencies. It suggests specific updates to maintain alignment.",
            'benefits': "Reduce documentation busywork by 62%. Decrease implementation errors by 45%. Improve cross-team alignment with 85% fewer documentation-related questions.",
            'call_to_action': f"Start a 14-day trial with your actual documents to measure time savings."
        }

        return json.dumps(messaging)

    def _generate_change_messaging(self, content, changes):
        """Generate messaging for project changes"""
        prd = content.get('prd', {})

        # Extract project name
        project_name = prd.get('name', 'Project')

        # Identify main change type
        has_new_feature = False
        feature_name = "features"
        if changes.get('prd', {}).get('added'):
            has_new_feature = True
            feature_name = changes['prd']['added'][0].replace('_', ' ')

        # Format the messaging
        if has_new_feature:
            messaging = {
                'headline': f"New: {feature_name} saves 2+ hours weekly",
                'pain_point': "Teams waste time manually tracking document changes and suggesting updates.",
                'solution': f"The new {feature_name} feature automatically detects changes and suggests specific updates. It reduces manual reconciliation work by 75% and improves documentation accuracy by 62%.",
                'call_to_action': f"Enable {feature_name} in your project settings today."
            }
        else:
            messaging = {
                'headline': f"{project_name} now 3x faster",
                'pain_point': "Processing large document sets previously took too long.",
                'solution': f"We've optimized the core engine to process documents 3x faster. This update also improves accuracy by 28% and adds support for 5 new document types.",
                'call_to_action': "Update to the latest version to access these improvements."
            }

        return json.dumps(messaging)

    def _has_changes(self, doc_changes):
        """Check if a document has any changes"""
        return (
            len(doc_changes.get('added', [])) > 0 or 
            len(doc_changes.get('modified', [])) > 0 or 
            len(doc_changes.get('removed', [])) > 0
        )