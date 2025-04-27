# services/change_impact_analyzer.py
import json
import logging
from models import Project
from flask import current_app
import anthropic

logger = logging.getLogger(__name__)

class ChangeImpactAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def analyze(self, changes):
        """
        Analyze the impact of detected changes on project focus using Claude

        Args:
            changes (dict): Changes detected in project content

        Returns:
            str: JSON string with impact analysis
        """
        # Get the latest project for context
        latest_project = Project.query.order_by(Project.timestamp.desc()).first()

        if not latest_project:
            return json.dumps({
                'impact_level': 'unknown',
                'focus_maintained': True,
                'analysis': 'Initial project setup - no impact to analyze'
            })

        # Calculate basic impact metrics
        impact_metrics = self._calculate_impact_metrics(changes)

        # If changes are minimal, use rule-based analysis
        if impact_metrics['total_changes'] <= 1:
            return self._rule_based_analysis(impact_metrics, latest_project)

        # Initialize Claude client
        try:
            api_key = current_app.config.get('CLAUDE_API_KEY')
            model = current_app.config.get('CLAUDE_MODEL', 'claude-3-opus-20240229')
            client = anthropic.Anthropic(api_key=api_key)  # Make sure no extra parameters are here
        except Exception as e:
            self.logger.error(f"Error initializing Claude client: {str(e)}")
            # Fall back to rule-based analysis
            return self._rule_based_analysis(impact_metrics, latest_project)

        # Format context for Claude
        project_content = latest_project.get_content_dict()
        context = self._format_context(project_content, changes)

        # Create prompt for Claude
        prompt = f"""
        I need to analyze the impact of changes on a project and determine if they maintain the project's focus.

        Here is the project context:
        {context}

        The following changes have been detected:
        {json.dumps(changes, indent=2)}

        Basic metrics:
        {json.dumps(impact_metrics, indent=2)}

        Please analyze these changes and determine:
        1. The overall impact level (minor, moderate, major)
        2. Whether the changes maintain the project's focus
        3. A brief analysis explaining your assessment

        Format the response as JSON with the following structure:
        {{
            "impact_level": "minor|moderate|major",
            "focus_maintained": true|false,
            "analysis": "Brief explanation of the impact assessment"
        }}

        Focus your analysis on whether these changes:
        - Stay true to the original project goals
        - Address the same customer pain points
        - Represent natural evolution vs. scope creep
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
                # Add metrics to the response
                result = json.loads(json_str)
                result['metrics'] = impact_metrics
                return json.dumps(result)
            else:
                self.logger.error("Could not find JSON in Claude response")
                return self._rule_based_analysis(impact_metrics, latest_project)

        except Exception as e:
            self.logger.error(f"Error analyzing change impact with Claude: {str(e)}")
            # Fall back to rule-based analysis
            return self._rule_based_analysis(impact_metrics, latest_project)

    def _format_context(self, content, changes):
        """Format content as context for Claude"""
        context = []

        # Add PRD information
        prd = content.get('prd', {})
        if prd:
            context.append("== Product Requirements Document (PRD) ==")
            for key, value in prd.items():
                if isinstance(value, str) and value:
                    if len(value) > 200:
                        value = value[:200] + "..."
                    context.append(f"{key.replace('_', ' ').title()}: {value}")

        # Add strategy information
        strategy = content.get('strategy', {})
        if strategy:
            context.append("\n== Strategy Document ==")
            for key, value in strategy.items():
                if isinstance(value, str) and value:
                    if len(value) > 200:
                        value = value[:200] + "..."
                    context.append(f"{key.replace('_', ' ').title()}: {value}")

        # Add PRFAQ information (summarized)
        prfaq = content.get('prfaq', {})
        if prfaq:
            context.append("\n== Press Release / FAQ (Summary) ==")
            if 'press_release' in prfaq:
                pr = prfaq['press_release']
                context.append(f"Press Release: {pr[:150]}..." if len(pr) > 150 else pr)

        return "\n".join(context)

    def _calculate_impact_metrics(self, changes):
        """Calculate metrics to quantify change impact"""
        metrics = {
            'total_changes': 0,
            'docs_changed': 0,
            'tickets_changed': 0,
            'change_distribution': {}
        }

        # Count total changes
        for doc_type, doc_changes in changes.items():
            doc_total = len(doc_changes.get('added', [])) + len(doc_changes.get('modified', [])) + len(doc_changes.get('removed', []))
            metrics['total_changes'] += doc_total

            if doc_total > 0:
                metrics['docs_changed'] += 1

            if doc_type == 'tickets':
                metrics['tickets_changed'] = doc_total

            # Track distribution
            metrics['change_distribution'][doc_type] = {
                'added': len(doc_changes.get('added', [])),
                'modified': len(doc_changes.get('modified', [])),
                'removed': len(doc_changes.get('removed', []))
            }

        return metrics

    def _rule_based_analysis(self, metrics, project):
        """Rule-based impact analysis"""
        # Determine impact level
        total = metrics['total_changes']
        docs_changed = metrics['docs_changed']

        if total == 0:
            impact_level = 'none'
        elif total <= 3 and docs_changed <= 1:
            impact_level = 'minor'
        elif total <= 10 and docs_changed <= 2:
            impact_level = 'moderate'
        else:
            impact_level = 'major'

        # Check if changes are to strategy (which might affect focus)
        strategy_changes = metrics['change_distribution'].get('strategy', {})
        strategy_total = strategy_changes.get('added', 0) + strategy_changes.get('modified', 0) + strategy_changes.get('removed', 0)

        # Check if PRD has major changes
        prd_changes = metrics['change_distribution'].get('prd', {})
        major_prd_changes = prd_changes.get('added', 0) > 2 or prd_changes.get('removed', 0) > 2

        # Determine if focus is maintained
        focus_maintained = True
        analysis = "Changes appear to maintain project focus."

        if strategy_total > 0:
            focus_maintained = False
            analysis = "Strategy changes detected. Project focus may have shifted. Review project description to ensure alignment."
        elif major_prd_changes:
            focus_maintained = False
            analysis = "Significant PRD changes detected. Project scope may have changed. Review project description and ensure tickets are aligned."
        elif impact_level == 'major':
            analysis = "Significant changes detected. Continue monitoring for scope creep and ensure alignment with original project goals."

        return json.dumps({
            'impact_level': impact_level,
            'focus_maintained': focus_maintained,
            'analysis': analysis,
            'metrics': metrics
        })