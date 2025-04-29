# services/document_validator.py
# This file contains the improved DocumentValidator class with more flexibility

import logging

class DocumentValidator:
    """Validate structured document content against flexible templates"""

    def __init__(self):
        """Initialize the DocumentValidator with a logger and templates"""
        self.logger = logging.getLogger(__name__)
        self.templates = self._define_templates()

    def _define_templates(self):
        """
        Define document templates with suggested (not required) sections

        Returns:
            dict: Flexible templates for different document types
        """
        return {
            'prd': {
                'suggested': ['name', 'overview', 'problem_statement', 'solution', 'requirements', 
                              'timeline', 'success_metrics', 'scope'],
                'minimum_suggested': 3,  # Minimum number of suggested sections for a valid document
                'suggested_length': {
                    'overview': (50, 2000),          # More flexible length ranges
                    'problem_statement': (20, 1000),
                    'solution': (50, 2000),
                    'requirements': (50, 5000)
                }
            },
            'prfaq': {
                'suggested': ['name', 'press_release', 'frequently_asked_questions'],
                'minimum_suggested': 2,
                'suggested_length': {
                    'press_release': (100, 2000),
                    'frequently_asked_questions': (2, 30)  # Min, max items
                }
            },
            'strategy': {
                'suggested': ['name', 'vision', 'approach', 'business_value', 'goals', 'timeline'],
                'minimum_suggested': 2,
                'suggested_length': {
                    'vision': (20, 500),
                    'approach': (50, 1000),
                    'business_value': (20, 1000)
                }
            },
            'generic': {  # Fallback for any document type
                'suggested': ['name', 'content'],
                'minimum_suggested': 1,
                'suggested_length': {}
            }
        }

    def validate_document(self, doc_content, doc_type):
        """
        Validate document content against flexible template

        Args:
            doc_content (dict): Structured document content
            doc_type (str): Document type

        Returns:
            dict: Validation results with suggestions
        """
        # Use generic template if doc_type not defined or unknown
        if not doc_type or doc_type not in self.templates:
            doc_type = 'generic'
            template = self.templates['generic']
        else:
            template = self.templates[doc_type]

        # Count how many suggested sections are present
        suggested_sections = template['suggested']
        present_suggested = [section for section in suggested_sections if section in doc_content and doc_content[section]]
        missing_suggested = [section for section in suggested_sections if section not in doc_content or not doc_content[section]]

        # Check if document has minimum number of suggested sections
        minimum_suggested = template.get('minimum_suggested', 1)
        has_minimum_sections = len(present_suggested) >= minimum_suggested

        # Check suggested section lengths (not enforced, just for suggestions)
        length_suggestions = []
        for section, (min_len, max_len) in template.get('suggested_length', {}).items():
            if section in doc_content:
                content = doc_content[section]

                if isinstance(content, str):
                    # Check string length
                    content_len = len(content)
                    if content_len < min_len:
                        length_suggestions.append({
                            'section': section,
                            'suggestion': 'consider_expanding',
                            'value': content_len,
                            'recommendation': f"Consider expanding to at least {min_len} characters for better clarity"
                        })
                    elif content_len > max_len:
                        length_suggestions.append({
                            'section': section,
                            'suggestion': 'consider_condensing',
                            'value': content_len,
                            'recommendation': f"Consider condensing to around {max_len} characters for better readability"
                        })
                elif isinstance(content, list):
                    # Check list length
                    content_len = len(content)
                    if content_len < min_len:
                        length_suggestions.append({
                            'section': section,
                            'suggestion': 'consider_adding_items',
                            'value': content_len,
                            'recommendation': f"Consider adding more items (suggested minimum: {min_len})"
                        })
                    elif content_len > max_len:
                        length_suggestions.append({
                            'section': section,
                            'suggestion': 'consider_reducing_items',
                            'value': content_len,
                            'recommendation': f"Consider reducing the number of items for better focus (suggested maximum: {max_len})"
                        })

        # Overall document assessment
        if not has_minimum_sections:
            document_suggestion = f"Document appears to be missing key sections for a {doc_type.upper()}. " + \
                                 f"Consider adding some of the following: {', '.join(missing_suggested[:3])}"
        elif length_suggestions:
            document_suggestion = f"Document structure looks good, but some sections could be improved for better readability."
        else:
            document_suggestion = f"Document structure appears to be a good fit for a {doc_type.upper()}."

        # Return validation results with helpful suggestions, not strict requirements
        return {
            'valid': True,  # Always consider document valid, just offer suggestions
            'identified_type': doc_type,
            'present_sections': present_suggested,
            'suggested_additions': missing_suggested[:3] if missing_suggested else [],
            'length_suggestions': length_suggestions,
            'overall_suggestion': document_suggestion
        }

    def suggest_improvements(self, validation_result, doc_content, doc_type):
        """
        Suggest content improvements based on validation results

        Args:
            validation_result (dict): Results from validate_document
            doc_content (dict): Document content
            doc_type (str): Document type

        Returns:
            list: Improvement suggestions
        """
        suggestions = []

        # Suggestions for missing typical sections
        for section in validation_result.get('suggested_additions', []):
            suggestions.append({
                'type': 'suggested_section',
                'section': section,
                'suggestion': f"Consider adding a {section.replace('_', ' ')} section",
                'examples': self._get_section_examples(section, doc_type)
            })

        # Suggestions for length improvements
        for issue in validation_result.get('length_suggestions', []):
            section = issue['section']
            suggestions.append({
                'type': issue['suggestion'],
                'section': section,
                'suggestion': f"{issue['recommendation']}",
                'examples': self._get_section_examples(section, doc_type) if issue['suggestion'] in ['consider_expanding', 'consider_adding_items'] else None
            })

        # Document type specific suggestions
        if doc_type == 'prd':
            # Suggest adding metrics if missing
            if 'problem_statement' in doc_content and not any(metric in doc_content.get('problem_statement', '').lower() 
                        for metric in ['%', 'percent', 'hour', 'day', 'week', 'month', 'increase', 'decrease']):
                suggestions.append({
                    'type': 'add_metrics',
                    'section': 'problem_statement',
                    'suggestion': "Consider adding quantifiable metrics to strengthen the business case",
                    'examples': ["Teams waste 4+ hours weekly reconciling inconsistent documentation",
                               "This process leads to a 28% increase in implementation errors",
                               "Project timelines are extended by 2-3 weeks on average"]
                })

        elif doc_type == 'prfaq':
            # Suggest common FAQs if fewer than expected
            if 'frequently_asked_questions' in doc_content and isinstance(doc_content['frequently_asked_questions'], list):
                faqs = doc_content['frequently_asked_questions']
                if len(faqs) < 5:
                    suggestions.append({
                        'type': 'add_faqs',
                        'section': 'frequently_asked_questions',
                        'suggestion': "Consider adding more FAQs to address common customer questions",
                        'examples': ["What problem does this solve?", 
                                  "How much time/money will this save?", 
                                  "How does this compare to alternatives?",
                                  "What resources are required to implement this?",
                                  "When will this be available?"]
                    })

        return suggestions

    def _get_section_examples(self, section, doc_type):
        """
        Get examples for document sections

        Args:
            section (str): Section name
            doc_type (str): Document type

        Returns:
            str or list: Example content for the section
        """
        examples = {
            'prd': {
                'overview': "The Document Sync Tool is a system that automatically synchronizes documentation across different platforms to ensure consistency and save teams time.",
                'problem_statement': "Teams waste 4+ hours weekly reconciling inconsistent documentation, leading to a 28% increase in implementation errors and 2-3 week project delays.",
                'solution': "Our system monitors connected documents for changes and automatically suggests updates to maintain alignment across the entire documentation ecosystem.",
                'requirements': "The system must: 1) Connect to major documentation platforms (Jira, Confluence, Google Docs), 2) Monitor documents for changes, 3) Suggest specific updates to maintain alignment, and 4) Provide a simple interface for approving changes."
            },
            'prfaq': {
                'press_release': "FOR IMMEDIATE RELEASE: Introducing Document Sync Tool, the first documentation synchronization system that automatically keeps your PRDs, tickets, and strategy documents perfectly aligned.",
                'frequently_asked_questions': [
                    "Q: What problem does this solve?\nA: Teams waste hours weekly reconciling inconsistent documentation.",
                    "Q: How does it work?\nA: We connect to your documentation systems and monitor changes, then suggest updates."
                ]
            },
            'strategy': {
                'vision': "Create a world where documentation is always accurate and teams never waste time on reconciliation.",
                'approach': "Build connectors to popular documentation systems and use NLP to identify inconsistencies.",
                'business_value': "Save teams 4+ hours per week and reduce implementation errors by 45%."
            }
        }

        if doc_type in examples and section in examples[doc_type]:
            return examples[doc_type][section]

        return None