# integrations/content_extractor.py
# Enhanced ContentExtractor with LLM-based document structure validation
# Using direct API calls and robust JSON handling

import re
import json
import logging
import requests  # For direct API calls
from collections import defaultdict
from flask import current_app
from prompts import get_prompt

class ContentExtractor:
    """Extract structured content from different document types using a generic approach followed by LLM review"""

    def __init__(self):
        """Initialize the ContentExtractor with a logger"""
        self.logger = logging.getLogger(__name__)

    def extract_structure(self, content, doc_type=None):
        """
        Extract structured content with a generic heading-based parser followed by LLM review

        Args:
            content (str): Raw document content
            doc_type (str, optional): Document type hint (not required for generic extraction)

        Returns:
            dict: Structured content with semantically organized sections
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

        # Now, perform LLM-based review to improve the structure
        if len(sections) > 2:  # Only if we have some sections to work with beyond just 'name'
            try:
                initial_section_count = len(sections)
                self.logger.info(f"Starting LLM structure review with {initial_section_count} sections")

                sections = self._llm_structure_review(sections, content, doc_type)

                final_section_count = len(sections)
                self.logger.info(f"Completed LLM structure review: {initial_section_count} → {final_section_count} sections")
            except Exception as e:
                self.logger.error(f"Error during LLM structure review: {str(e)}")
                # Continue with the current sections if LLM review fails
                pass

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

    def _llm_structure_review(self, sections, original_content, doc_type=None):
        """
        Use LLM to review and improve the document structure using direct API calls

        Args:
            sections (dict): Initially extracted sections
            original_content (str): Raw document content
            doc_type (str, optional): Document type hint

        Returns:
            dict: Improved sections with semantic organization
        """
        try:
            # Get Claude API key from application config
            api_key = current_app.config.get('CLAUDE_API_KEY')
            model = current_app.config.get('CLAUDE_MODEL', 'claude-3-opus-20240229')

            if not api_key:
                self.logger.warning("No Claude API key available. Skipping LLM structure review.")
                return sections

            # Prepare the document structure for review
            sections_str = json.dumps(sections, indent=2)

            # Calculate content length for context
            content_length = len(original_content)

            # Get the document structure review prompt from centralized prompt system
            prompt = get_prompt(
                'document_structure',
                None,  # No general context needed
                sections=sections_str,
                doc_type=doc_type if doc_type else "Unknown",
                content_length=content_length
            )

            # Add special instructions for Claude to return ONLY valid JSON
            prompt += "\n\nIMPORTANT: Your response must be ONLY a valid, parseable JSON object with no other text. No explanations, no other formatting, just the JSON structure."

            # Log the action
            self.logger.info(f"Making direct API call to Claude for document structure review")

            # Use direct API call with known working approach
            try:
                response = requests.post(
                    'https://api.anthropic.com/v1/messages',
                    json={
                        'model': model,
                        'max_tokens': 1500,
                        'messages': [{'role': 'user', 'content': prompt}]
                    },
                    headers={
                        'x-api-key': api_key,
                        'anthropic-version': '2023-06-01',
                        'Content-Type': 'application/json'
                    },
                    timeout=30  # 30 second timeout
                )

                # Check response status
                if response.status_code != 200:
                    self.logger.error(f"Claude API error: {response.status_code} - {response.text}")
                    return sections

                # Parse response
                response_data = response.json()
                console.log(response_data)
                # Log the raw response content for debugging
                self.logger.debug(f"Raw Claude response: {response_content[:200]}...")

                # Clean up the JSON - ensure it's properly formatted
                try:
                    # First try: look for valid JSON in the response
                    import re
                    json_match = re.search(r'({[\s\S]*})', response_content)

                    if json_match:
                        json_text = json_match.group(1)
                        # Preprocess the JSON text - fix common issues
                        json_text = json_text.replace('\n', ' ')  # Replace newlines with spaces
                        json_text = re.sub(r'\s+', ' ', json_text)  # Replace multiple spaces with single space

                        # Special debugging for the specific error you're seeing
                        self.logger.debug(f"JSON text starts with: {json_text[:20]}")
                        if json_text.startswith('{\n  "name"') or json_text.startswith('{ "name"'):
                            self.logger.debug("Found problematic JSON format, fixing...")
                            # Make sure we have a clean JSON opening
                            json_text = json_text.replace('{\n  "', '{"')
                            json_text = json_text.replace('{ "', '{"')

                        # Try to parse the JSON
                        self.logger.debug(f"Attempting to parse cleaned JSON: {json_text[:50]}...")
                        improved_sections = json.loads(json_text)

                        # Log success and section counts
                        self.logger.info(f"Successfully parsed JSON after cleaning!")
                        initial_count = len(sections)
                        improved_count = len(improved_sections)
                        self.logger.info(f"Section count: {initial_count} → {improved_count}")

                        return improved_sections
                    else:
                        self.logger.warning("Could not find valid JSON in Claude response")
                        return sections

                except Exception as e:
                    self.logger.error(f"Error parsing JSON from Claude: {str(e)}")
                    self.logger.error(f"First 20 chars of response: {response_content[:20]}")

                    # Super fallback - try something really simple
                    try:
                        self.logger.debug("Attempting JSON parse with extreme cleaning...")
                        # Just take everything that looks like JSON and force it
                        simple_json = response_content.replace('\n', ' ').strip()
                        if simple_json.startswith('```json'):
                            simple_json = simple_json.replace('```json', '', 1)
                        if simple_json.endswith('```'):
                            simple_json = simple_json[:-3]

                        # Force proper JSON start/end
                        if not simple_json.startswith('{'):
                            simple_json = '{' + simple_json
                        if not simple_json.endswith('}'):
                            simple_json = simple_json + '}'

                        # Try to parse this extremely cleaned version
                        improved_sections = json.loads(simple_json)
                        self.logger.info("Successfully parsed JSON with extreme cleaning!")
                        return improved_sections
                    except:
                        self.logger.error("All JSON parsing attempts failed")
                        return sections

                # Process the response with our enhanced robust JSON handling
                return self._process_claude_json_response(response_content, sections)

            except requests.exceptions.RequestException as req_error:
                self.logger.error(f"Request error when calling Claude API: {str(req_error)}")
                return sections

        except Exception as e:
            self.logger.error(f"Error in LLM structure review: {str(e)}")
            return sections  # Return original sections if LLM review fails

    def _process_claude_json_response(self, response_content, original_sections):
        """
        Process Claude's JSON response with robust error handling

        Args:
            response_content (str): The raw response text from Claude
            original_sections (dict): The original sections to return if parsing fails

        Returns:
            dict: The parsed improved sections or the original sections if parsing fails
        """
        # Find JSON in the response
        json_start = response_content.find('{')
        json_end = response_content.rfind('}') + 1

        if json_start == -1 or json_end == -1:
            self.logger.warning("Could not find JSON in Claude response")
            # Log a sample of the full response for debugging
            self.logger.debug(f"Full response content: {response_content}")
            return original_sections

        # Extract the JSON substring
        json_str = response_content[json_start:json_end]

        # Log the raw JSON string
        self.logger.debug(f"Raw JSON string: {json_str[:100]}...")  # First 100 chars

        try:
            # Clean the JSON string before parsing
            # Remove any leading/trailing whitespace or newlines
            cleaned_json = json_str.strip()

            # Try to parse the cleaned JSON
            improved_sections = json.loads(cleaned_json)
            self.logger.info(f"Successfully improved document structure: detected type={improved_sections.get('structured_type', 'unknown')}")

            # Log section counts for debugging
            initial_count = len(original_sections)
            improved_count = len(improved_sections)
            self.logger.info(f"Section count: {initial_count} → {improved_count}")

            return improved_sections
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON from Claude response: {str(e)}")

            # More aggressive cleaning - try to fix common JSON problems
            try:
                # Try to clean the JSON string more aggressively
                aggressive_clean = cleaned_json.replace('\n', '').replace('\r', '')
                self.logger.debug(f"Attempting aggressive JSON cleaning")

                # Try to parse again with aggressively cleaned JSON
                improved_sections = json.loads(aggressive_clean)
                self.logger.info(f"Successfully parsed JSON after aggressive cleaning")
                return improved_sections
            except json.JSONDecodeError:
                self.logger.error(f"JSON parsing still failed after aggressive cleaning")

            # If all parsing attempts fail, try to extract valid JSON using regex
            try:
                self.logger.debug(f"Attempting regex-based JSON extraction")
                # Look for well-formed JSON objects
                json_pattern = r'({[^{}]*(?:{[^{}]*}[^{}]*)*})'
                match = re.search(json_pattern, response_content)
                if match:
                    extracted_json = match.group(1)
                    improved_sections = json.loads(extracted_json)
                    self.logger.info(f"Successfully extracted JSON using regex")
                    return improved_sections
            except (json.JSONDecodeError, Exception) as regex_error:
                self.logger.error(f"Regex extraction failed: {str(regex_error)}")

            # Log problematic JSON for debugging
            self.logger.debug(f"Problematic JSON (first 500 chars): {json_str[:500]}...")

            # Final fallback: try to manually fix the most common JSON errors
            try:
                self.logger.debug(f"Attempting manual JSON repair")
                # Check if it's missing an opening or closing brace
                if not cleaned_json.startswith('{'):
                    cleaned_json = '{' + cleaned_json
                if not cleaned_json.endswith('}'):
                    cleaned_json = cleaned_json + '}'

                # Fix common quoting errors
                cleaned_json = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', cleaned_json)

                # Try parsing one last time
                improved_sections = json.loads(cleaned_json)
                self.logger.info(f"Successfully parsed JSON after manual repair")
                return improved_sections
            except json.JSONDecodeError:
                self.logger.error(f"All JSON parsing attempts failed")

            # If all parsing attempts fail, return original sections
            return original_sections

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