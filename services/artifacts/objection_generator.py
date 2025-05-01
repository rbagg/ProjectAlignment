# services/artifacts/objection_generator.py
import json
import logging
from models import Project
from .base_generator import BaseGenerator
from prompts import get_prompt

class ObjectionGenerator(BaseGenerator):
    """
    Generates critical objections to project artifacts.
    Core feature for challenging assumptions and improving communication.
    """

    def get_latest(self):
        """
        Get latest objections from database.
        Required implementation of abstract method from BaseGenerator.

        Returns:
            dict: Latest objections or None
        """
        project = Project.query.order_by(Project.timestamp.desc()).first()
        if not project:
            return None

        return {
            'description': project.get_description_objections_list(),
            'internal': project.get_internal_objections_list(),
            'external': project.get_external_objections_list()
        }

    def generate(self, project_content, artifact_type='description'):
        """
        Generate objections for project content.
        Required implementation of abstract method from BaseGenerator.

        Args:
            project_content (str): JSON string of project content
            artifact_type (str): Type of artifact to generate objections for

        Returns:
            str: JSON string of objections
        """
        content = self.parse_content(project_content)

        # For this method, we'll just use generate_for_artifact
        # with a dummy artifact content since that's what we actually want to use
        dummy_artifact = {"type": artifact_type}
        return self.generate_for_artifact(content, dummy_artifact, artifact_type)

    def generate_for_artifact(self, project_content, artifact_content, artifact_type):
        """
        Generate thought-provoking objections that challenge core assumptions

        Args:
            project_content (dict): The project content
            artifact_content (dict): The artifact content to critique
            artifact_type (str): Type of artifact ('description', 'internal', 'external')

        Returns:
            str: JSON string of objections
        """
        # Format context for the improved objection prompt
        context = self._format_context(project_content)

        # Convert artifact content to a formatted string
        artifact_string = json.dumps(artifact_content, indent=2)

        # Create a more challenging prompt focused on assumptions and critical thinking
        prompt = f"""
        # Critical Thinking Challenge

        You are a Critical Assumption Challenger tasked with identifying the core assumptions, potential blindspots, 
        and intellectual weaknesses in a project document. Your goal is to force deeper thinking and protect
        against groupthink by raising substantive objections that go beyond mere format issues.

        ## Project Context
        {context}

        ## Artifact to Evaluate
        {artifact_string}

        ## Your Task
        Generate 3-4 substantial objections that:

        1. Challenge fundamental assumptions in the project thinking
        2. Identify potential blind spots that could derail success
        3. Question the "taken for granted" aspects that haven't been justified
        4. Push for intellectual rigor and clarity of thought
        5. Identify where scope might be too broad or focus is lacking

        FORMAT:
        Provide your response as a JSON array of objection objects with these properties:
        - "title": Brief, incisive name of the issue (3-6 words)
        - "explanation": Clear articulation of what's being assumed or overlooked
        - "impact": Specific business or project consequences of this issue
        - "challenging_question": A thought-provoking question that forces deeper thinking on this issue

        IMPORTANT:
        - Focus on substantive thinking issues, not superficial formatting concerns
        - Do NOT simply point out "missing sections" - dig into the intellectual foundations
        - Avoid objections that can be addressed with simple additions - look for conceptual problems
        - Each objection should make the reader uncomfortable and force them to think harder
        - If this is an external-facing artifact, consider customer skepticism and market realities
        """

        # Generate objections with the improved approach
        objections_json = self.generate_with_claude(
            prompt=prompt,
            fallback_method=self._substantive_fallback_objections,
            fallback_args={'artifact_type': artifact_type, 'artifact_content': artifact_content}
        )

        # Print debug info to help with troubleshooting
        print(f"GENERATED OBJECTIONS FOR {artifact_type}: {objections_json[:200]}...")

        return objections_json

    def _substantive_fallback_objections(self, artifact_type, artifact_content):
        """Provide substantive fallback objections that challenge thinking"""
        if artifact_type == 'description':
            return json.dumps([
                {
                    "title": "Solving Symptoms Not Cause",
                    "explanation": "The document focuses on synchronizing documentation but doesn't question whether the fundamental need for multiple document types is itself the problem. Could a single source of truth approach eliminate the need for synchronization entirely?",
                    "impact": "Building a complex synchronization system may create more overhead than redesigning the documentation approach from first principles.",
                    "challenging_question": "What if instead of syncing documents, we eliminated the need for multiple documents in the first place?"
                },
                {
                    "title": "Synchronization vs. Insight Gap",
                    "explanation": "The solution assumes teams primarily need technical alignment of documents, but the deeper problem might be the lack of shared understanding of goals and priorities across teams.",
                    "impact": "A system that technically aligns documentation might still leave teams misaligned on intent, priorities, and the 'why' behind decisions.",
                    "challenging_question": "Is the real problem document inconsistency or lack of shared context and understanding between teams?"
                },
                {
                    "title": "Tool Adoption Reality Check",
                    "explanation": "The artifact assumes teams will adopt and consistently use yet another tool in their workflow without addressing the behavioral and cultural reasons documentation falls out of sync.",
                    "impact": "If the underlying behavioral drivers aren't addressed, teams may continue old patterns even with a new tool, rendering it ineffective.",
                    "challenging_question": "What specific behavioral or cultural shifts must happen for this tool to actually be used consistently, regardless of its technical capabilities?"
                }
            ])
        elif artifact_type == 'internal':
            return json.dumps([
                {
                    "title": "Technical Debt Blindspot",
                    "explanation": "The message focuses on new features without addressing how this system will manage its own technical debt, particularly as the APIs and systems it connects to evolve.",
                    "impact": "Without an explicit technical debt strategy, the system might require constant maintenance to keep connectors working, eventually becoming a burden rather than a solution.",
                    "challenging_question": "How would this system handle the technical debt created by ongoing changes to all the systems it integrates with?"
                },
                {
                    "title": "Unaddressed Behavioral Change",
                    "explanation": "The messaging assumes technical solutions alone will drive adoption without addressing the cultural and behavioral changes required from teams.",
                    "impact": "Without a behavioral change strategy, teams may continue with familiar manual processes even with the new tool available.",
                    "challenging_question": "What specific behavioral changes are required from different roles, and how will you drive those changes beyond just making a tool available?"
                },
                {
                    "title": "Incremental Value Path Missing",
                    "explanation": "The plan presents a big-bang solution without a clear path to incremental value, making it difficult to validate assumptions early.",
                    "impact": "Without early validation points, the project risks delivering a comprehensive solution that doesn't actually solve the real problem.",
                    "challenging_question": "What is the minimum viable product that would deliver measurable value to one team, and how could you use that to validate your core assumptions?"
                }
            ])
        elif artifact_type == 'external':
            return json.dumps([
                {
                    "title": "Unexplored Competitive Landscape",
                    "explanation": "The messaging doesn't address how this solution fits within or differentiates from the broader market of documentation and workflow tools.",
                    "impact": "Prospects will immediately compare this to existing tools they already use, and without clear differentiation, will see this as redundant.",
                    "challenging_question": "Why would someone choose this over extending their existing documentation system, and how have you validated this differentiation?"
                },
                {
                    "title": "ROI Justification Gap",
                    "explanation": "The value proposition rests on time savings without addressing the adoption cost, training time, and integration effort required to realize those savings.",
                    "impact": "Without a clear time-to-value path and ROI calculation that includes all costs, customers will struggle to justify the investment.",
                    "challenging_question": "What is the total cost of implementation, including integration and behavior change, and at what point does a customer break even on their investment?"
                },
                {
                    "title": "Customer Validation Missing",
                    "explanation": "The messaging makes assumptions about customer needs and value perception without evidence of customer validation or testimonials.",
                    "impact": "Without demonstrated proof that real customers value this approach, prospects will be skeptical of claims and hesitant to adopt.",
                    "challenging_question": "Which specific customers have validated that this approach solves a problem they're willing to pay for, and what were their actual words?"
                }
            ])
        else:
            return json.dumps([
                {
                    "title": "Assumption vs. Evidence Gap",
                    "explanation": "The artifact makes several key assertions without distinguishing between validated facts and untested assumptions.",
                    "impact": "Building on unvalidated assumptions increases the risk of delivering a solution that doesn't address the actual problem.",
                    "challenging_question": "Which parts of this are validated with evidence, and which parts are assumptions that still need testing?"
                },
                {
                    "title": "Oversimplified Success Path",
                    "explanation": "The document presents a straightforward path to success without acknowledging the complexities, dependencies, and potential pitfalls.",
                    "impact": "Underestimating complexity leads to missed deadlines, scope creep, and frustrated stakeholders when reality proves more challenging.",
                    "challenging_question": "What are the three most likely ways this project could fail, and how are you proactively addressing each one?"
                },
                {
                    "title": "Missing Minimum Viable Test",
                    "explanation": "The approach doesn't include a clear, small-scale test that could validate core assumptions before full investment.",
                    "impact": "Without early validation, the project risks significant investment in a direction that might not deliver the expected value.",
                    "challenging_question": "What is the smallest experiment you could run in the next two weeks to test the most critical assumption underlying this project?"
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

    def _fallback_objections(self, artifact_type):
        """Provide fallback objections if Claude fails."""
        if artifact_type == 'description':
            return json.dumps([
                {
                    "title": "No Success Metrics",
                    "explanation": "The description lacks measurable KPIs to evaluate success.",
                    "impact": "Projects without metrics show 40% higher failure rates."
                },
                {
                    "title": "Alternatives Not Compared",
                    "explanation": "No explanation of why this approach beats alternatives.",
                    "impact": "Insufficient alternative analysis increases project pivots by 35%."
                },
                {
                    "title": "Integration Requirements Missing",
                    "explanation": "No mention of how this integrates with existing systems.",
                    "impact": "Integration planning gaps cause 50% of implementation delays."
                }
            ])
        elif artifact_type == 'internal':
            return json.dumps([
                {
                    "title": "Resource Requirements Unspecified",
                    "explanation": "Message doesn't detail team resources needed.",
                    "impact": "Resource planning gaps cause 30% of project delays."
                },
                {
                    "title": "No Timeline Provided",
                    "explanation": "No mention of key milestones or deadlines.",
                    "impact": "Timeline omissions lead to 35% of projects missing deadlines."
                },
                {
                    "title": "Success Metrics Undefined",
                    "explanation": "No specific KPIs for measuring project success.",
                    "impact": "Undefined metrics lead to 25% increase in scope creep."
                }
            ])
        elif artifact_type == 'external':
            return json.dumps([
                {
                    "title": "Value Not Quantified",
                    "explanation": "Mentions benefits without quantifying customer impact.",
                    "impact": "Non-quantified value props convert 35% worse than specific ones."
                },
                {
                    "title": "No Differentiation",
                    "explanation": "Doesn't explain advantages over competitor solutions.",
                    "impact": "Undifferentiated messaging reduces conversion by 28%."
                },
                {
                    "title": "Implementation Effort Unstated",
                    "explanation": "Doesn't address customer effort to implement.",
                    "impact": "Unstated implementation requirements increase sales cycle by 40%."
                }
            ])
        else:
            return json.dumps([
                {
                    "title": "Insufficient Detail",
                    "explanation": "The artifact lacks necessary detail for evaluation.",
                    "impact": "Insufficient detail leads to 40% more implementation questions."
                }
            ])

    def _generate_description_objections(self, project_content, description):
        """Generate objections to the project description."""
        context = self._format_context(project_content)

        # Convert artifact content to a formatted string
        artifact_string = json.dumps(description, indent=2)

        # Get objection generator prompt from centralized prompt system
        prompt = get_prompt('objection_generator', context, artifact=artifact_string, artifact_type='description')

        return self.generate_with_claude(
            prompt=prompt,
            fallback_method=self._fallback_objections,
            fallback_args={'artifact_type': 'description'}
        )

    def _generate_internal_objections(self, project_content, messaging):
        """Generate objections to the internal messaging."""
        context = self._format_context(project_content)

        # Convert artifact content to a formatted string
        artifact_string = json.dumps(messaging, indent=2)

        # Get objection generator prompt from centralized prompt system
        prompt = get_prompt('objection_generator', context, artifact=artifact_string, artifact_type='internal')

        return self.generate_with_claude(
            prompt=prompt,
            fallback_method=self._fallback_objections,
            fallback_args={'artifact_type': 'internal'}
        )

    def _generate_external_objections(self, project_content, messaging):
        """Generate objections to the external messaging."""
        context = self._format_context(project_content)

        # Convert artifact content to a formatted string
        artifact_string = json.dumps(messaging, indent=2)

        # Get objection generator prompt from centralized prompt system
        prompt = get_prompt('objection_generator', context, artifact=artifact_string, artifact_type='external')

        return self.generate_with_claude(
            prompt=prompt,
            fallback_method=self._fallback_objections,
            fallback_args={'artifact_type': 'external'}
        )