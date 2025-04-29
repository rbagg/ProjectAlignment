# integrations/content_extractor.py
# This file contains a more generic ContentExtractor class

import re
import logging
from collections import defaultdict

class ContentExtractor:
    """Extract structured content from different document types using a generic approach"""

    def __init__(self):
        """Initialize the ContentExtractor with a logger"""
        self.logger = logging.getLogger(__name__)

    def extract_structure(self, content, doc_type=None):
        """
        Extract structured content with a generic heading-based parser

        Args:
            content (str): Raw document content
            doc_type (str, optional): Document type hint (not required for generic extraction)

        Returns:
            dict: Structured content with sections
        """
        # First, try to identify the document title regardless of type
        title = self._extract_document_title(content)

        # Extract all sections based on headings
        sections = self._extract_all_sections(content)

        # Always include name/title
        sections['name'] = title

        # If we have a document type hint, we can do some post-processing
        if doc_type:
            sections = self._enhance_extraction(sections, content, doc_type)

        return sections

    def _extract_document_title(self, content):
        """
        Extract document title using various common patterns

        Args:
            content (str): Raw document content

        Returns:
            str: Document title
        """
        # Try several title patterns
        title_patterns = [
            r'^\s*#\s+(.+?)(?:\n|$)',                               # Markdown H1: # Title
            r'^\s*(.+?)\n=+\s*$',                                   # Markdown alternative H1: Title\n====
            r'^\s*(.+?)\n-+\s*$',                                   # Markdown alternative H2: Title\n----
            r'(?:^|\n)\s*(?:title|document|project):\s*(.+?)(?:\n|$)', # Explicit title field
            r'(?:^|\n)\s*#+\s*(\d+\.?\s*.+?)(?:\n|$)',             # Numbered section (e.g., "# 1. Title")
            r'(?:^|\n)\s*(\d+\.?\s*.+?)(?:\n|$)'                   # Just numbered (e.g., "1. Title")
        ]

        for pattern in title_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()

        # If no explicit title found, use the first line or a default
        first_line = content.strip().split('\n')[0]
        if first_line and len(first_line) < 100:  # Reasonable title length
            return first_line.strip()

        return "Untitled Document"

    def _extract_all_sections(self, content):
        """
        Extract all sections based on heading patterns

        Args:
            content (str): Raw document content

        Returns:
            dict: All extracted sections
        """
        sections = {}

        # Find all headings with content
        # This pattern looks for various heading formats:
        # 1. Markdown headings: # Heading
        # 2. Numbered headings: 1. Heading or 1.1. Heading
        # 3. Underlined headings: Heading\n====== or Heading\n------
        # 4. Bold headings: **Heading**
        heading_pattern = r'(?:^|\n)(?:(?:##+\s*(.+?))|(?:\d+(?:\.\d+)*\.?\s*(.+?))|(?:([^\n]+)\n(?:=+|-+))|(?:\*\*(.+?)\*\*))(?:\n|$)'

        # Find all matches
        matches = list(re.finditer(heading_pattern, content, re.MULTILINE))

        # Process each heading and its content
        for i, match in enumerate(matches):
            # Get the heading (whichever group matched)
            heading = next((g for g in match.groups() if g), "").strip()

            # Normalize the heading as a key
            section_key = self._normalize_heading(heading)

            # Find the content for this section (up to the next heading)
            if i < len(matches) - 1:
                next_match = matches[i + 1]
                section_content = content[match.end():next_match.start()].strip()
            else:
                section_content = content[match.end():].strip()

            # Store the section
            if section_key and section_content:
                sections[section_key] = section_content

        # If no sections found, try to identify bullet point based sections
        if not sections:
            sections = self._extract_bullet_point_sections(content)

        return sections

    def _extract_bullet_point_sections(self, content):
        """
        Extract sections from bullet points with bold titles

        Args:
            content (str): Raw document content

        Returns:
            dict: Sections extracted from bullet points
        """
        sections = {}

        # Look for bullet points with bold titles
        # Pattern: - **Title:** Content
        bullet_pattern = r'(?:^|\n)\s*-\s*\*\*([^:]+):\*\*\s*(.+?)(?=\n\s*-\s*\*\*|$)'

        for match in re.finditer(bullet_pattern, content, re.DOTALL):
            section_name = match.group(1).strip()
            section_content = match.group(2).strip()

            if section_name and section_content:
                section_key = self._normalize_heading(section_name)
                sections[section_key] = section_content

        return sections

    def _normalize_heading(self, heading):
        """
        Convert heading to a normalized section name

        Args:
            heading (str): Raw heading text

        Returns:
            str: Normalized section name
        """
        if not heading:
            return ""

        # Remove numbers from the start of headings (e.g., "1. Introduction" -> "Introduction")
        heading = re.sub(r'^\d+(?:\.\d+)*\.?\s*', '', heading)

        # Remove special characters and convert to lowercase
        normalized = re.sub(r'[^a-zA-Z0-9 ]', '', heading.lower())

        # Replace spaces with underscores
        normalized = re.sub(r'\s+', '_', normalized.strip())

        return normalized

    def _enhance_extraction(self, sections, content, doc_type):
        """
        Enhance extraction based on document type hints

        Args:
            sections (dict): Already extracted sections
            content (str): Raw document content
            doc_type (str): Document type hint

        Returns:
            dict: Enhanced sections
        """
        # Look for common sections that might be missing based on doc_type
        if doc_type == 'prd':
            # Try to find problem/challenge sections if missing
            if 'problem' not in sections and 'problem_statement' not in sections:
                problem_text = self._find_problem_statement(content)
                if problem_text:
                    sections['problem_statement'] = problem_text

            # Look for solution approach if missing
            if 'solution' not in sections and 'approach' not in sections:
                solution_text = self._find_solution_approach(content)
                if solution_text:
                    sections['solution'] = solution_text

        elif doc_type == 'prfaq':
            # Try to extract FAQs as a list
            if 'frequently_asked_questions' not in sections:
                faqs = self._extract_faqs(content)
                if faqs:
                    sections['frequently_asked_questions'] = faqs

            # Try to identify press release
            if 'press_release' not in sections:
                pr_text = self._find_press_release(content)
                if pr_text:
                    sections['press_release'] = pr_text

        elif doc_type == 'strategy':
            # Look for vision, approach, business value
            if 'vision' not in sections:
                vision_text = self._find_vision(content)
                if vision_text:
                    sections['vision'] = vision_text

            if 'approach' not in sections and 'strategy' not in sections:
                approach_text = self._find_approach(content)
                if approach_text:
                    sections['approach'] = approach_text

            if 'business_value' not in sections:
                value_text = self._find_business_value(content)
                if value_text:
                    sections['business_value'] = value_text

        return sections

    def _find_problem_statement(self, content):
        """Find problem statement in content"""
        # Try various patterns to find problem statements
        problem_patterns = [
            # Look for problem section
            r'(?:problem|problem statement|challenges).*?[:\n](.*?)(?:\n\n|\n#|\n\d|$)',
            # Look for "Problem" in bullet points
            r'- .*?(?:problem|issue|challenge).*?:?\s*(.*?)(?:\n-|\n\n|$)',
            # Look for "Current State" with problem mentioned
            r'current state.*?[:\n](.*?)(?:\n-|\n\n|$)',
            # Look for pain point bullet
            r'- .*?(?:pain point|challenge).*?:?\s*(.*?)(?:\n-|\n\n|$)'
        ]

        for pattern in problem_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

        return None

    def _find_solution_approach(self, content):
        """Find solution approach in content"""
        # Try various patterns to find solution approaches
        solution_patterns = [
            # Look for solution section
            r'(?:solution|approach|proposed solution).*?[:\n](.*?)(?:\n\n|\n#|\n\d|$)',
            # Look for "Solution" in bullet points
            r'- .*?(?:solution|approach).*?:?\s*(.*?)(?:\n-|\n\n|$)',
            # Look for "Opportunity" with solution mentioned
            r'opportunity.*?[:\n](.*?)(?:\n-|\n\n|$)',
            # Look for objectives section
            r'(?:objectives|goals).*?[:\n](.*?)(?:\n\n|\n#|\n\d|$)'
        ]

        for pattern in solution_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

        return None

    def _extract_faqs(self, content):
        """Extract FAQs as a list of question/answer pairs"""
        faqs = []

        # Try to find Q&A patterns
        qa_patterns = [
            # Q: ... A: ... format
            r'(?:^|\n)(?:Q:|Question:)\s*(.*?)\n+(?:A:|Answer:)\s*(.*?)(?=\n+(?:Q:|Question:)|\n\n\n|$)',
            # Numbered Q&A format
            r'(?:^|\n)(?:\d+\.\s*)(.*?)\n+(.*?)(?=\n+\d+\.\s*|$)',
            # Bold Q&A format
            r'(?:^|\n)(?:\*\*Q:|Question:\*\*)\s*(.*?)\n+(?:\*\*A:|Answer:\*\*)\s*(.*?)(?=\n+\*\*Q:|$)'
        ]

        for pattern in qa_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                question = match.group(1).strip()
                answer = match.group(2).strip()

                # Only add if it looks like a proper Q&A
                if len(question) > 5 and len(answer) > 5:
                    faqs.append({
                        'question': question,
                        'answer': answer
                    })

        return faqs if faqs else None

    def _find_press_release(self, content):
        """Find press release section in content"""
        # Try various patterns to find press release
        pr_patterns = [
            # Look for press release section
            r'(?:press release|announcement|for immediate release).*?[:\n](.*?)(?=\n\n\n|\n#|\n\d|$)',
            # Look for heading followed by short paragraphs
            r'(?:^|\n)#+\s*([^#\n]{10,100})\n\n([^#]{50,500})(?=\n\n\n|\n#|\n\d|$)'
        ]

        for pattern in pr_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                # If the pattern has multiple groups, combine them
                if match.lastindex and match.lastindex > 1:
                    return match.group(1).strip() + "\n\n" + match.group(2).strip()
                return match.group(1).strip()

        return None

    def _find_vision(self, content):
        """Find vision statement in content"""
        # Try various patterns to find vision
        vision_patterns = [
            # Look for vision section
            r'(?:vision|mission).*?[:\n](.*?)(?:\n\n|\n#|\n\d|$)',
            # Look for "Vision" in bullet points
            r'- .*?(?:vision|mission).*?:?\s*(.*?)(?:\n-|\n\n|$)',
        ]

        for pattern in vision_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

        return None

    def _find_approach(self, content):
        """Find approach or strategy in content"""
        # Try various patterns to find approach
        approach_patterns = [
            # Look for approach section
            r'(?:approach|strategy|methodology).*?[:\n](.*?)(?:\n\n|\n#|\n\d|$)',
            # Look for "Approach" in bullet points
            r'- .*?(?:approach|strategy).*?:?\s*(.*?)(?:\n-|\n\n|$)',
        ]

        for pattern in approach_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

        return None

    def _find_business_value(self, content):
        """Find business value in content"""
        # Try various patterns to find business value
        value_patterns = [
            # Look for business value section
            r'(?:business value|business impact|value proposition).*?[:\n](.*?)(?:\n\n|\n#|\n\d|$)',
            # Look for "Value" in bullet points
            r'- .*?(?:business value|impact|benefit).*?:?\s*(.*?)(?:\n-|\n\n|$)',
        ]

        for pattern in value_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

        return None