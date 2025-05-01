# integrations/content_extractor.py
# Completely reimagined content extractor that uses Claude to understand any document type
import re
import json
import logging
import requests
from flask import current_app

class ContentExtractor:
    """
    A simplified, reliable content extractor that uses Claude to understand any document format.
    Rather than trying to parse and structure the document ourselves, we let Claude do the heavy lifting.
    """

    def __init__(self):
        """Initialize the ContentExtractor with a logger"""
        self.logger = logging.getLogger(__name__)

    def extract_structure(self, content, doc_type=None):
        """
        Extract structured content using Claude as the primary analyzer

        Args:
            content (str): Raw document content
            doc_type (str, optional): Document type hint (not required)

        Returns:
            dict: Structured content as organized by Claude
        """
        # First, get the basic document title
        title = self._extract_document_title(content)

        # Create a basic structure with the title
        basic_structure = {
            "name": title,
            "content_length": len(content),
            "raw_excerpt": content[:200] + ("..." if len(content) > 200 else "")
        }

        # Then use Claude to analyze and structure the full document
        try:
            # If we have a Claude API key, use it to analyze the document
            api_key = current_app.config.get('CLAUDE_API_KEY')
            if api_key:
                self.logger.info(f"Using Claude to analyze document, length: {len(content)} chars")
                enhanced_structure = self._claude_document_analysis(content, doc_type, basic_structure)
                if enhanced_structure:
                    self.logger.info(f"Successfully analyzed document with Claude")
                    return enhanced_structure
                else:
                    self.logger.warning("Claude analysis failed, returning basic structure")
            else:
                self.logger.warning("No Claude API key available")
        except Exception as e:
            self.logger.error(f"Error in Claude analysis: {str(e)}")

        # Always have a fallback - extract sections based on headings if Claude fails
        self.logger.info("Falling back to basic section extraction")
        sections = self._extract_all_sections(content)
        sections.update(basic_structure)
        return sections

    def _extract_document_title(self, content):
        """Extract a document title from content"""
        # Try to find a title from the first non-empty line
        lines = content.strip().split('\n')
        for line in lines:
            clean_line = line.strip()
            if clean_line and len(clean_line) < 100:
                # Remove markdown heading symbols
                clean_line = re.sub(r'^#+\s*', '', clean_line)
                return clean_line

        return "Untitled Document"

    def _extract_all_sections(self, content):
        """Basic section extraction as a fallback"""
        sections = {}

        # Simple heading pattern for markdown or structured text
        heading_pattern = r'(?:^|\n)(?:#+\s*(.+?)|(\d+(?:\.\d+)*\.?\s*.+?))(?:\n|$)'

        matches = list(re.finditer(heading_pattern, content, re.MULTILINE))

        # Process each heading and its content
        for i, match in enumerate(matches):
            heading = next((g for g in match.groups() if g), "").strip()

            # Normalize the heading as a key
            section_key = re.sub(r'[^a-zA-Z0-9]', '_', heading.lower()).strip('_')

            # Find the content for this section (up to the next heading)
            if i < len(matches) - 1:
                next_match = matches[i + 1]
                section_content = content[match.end():next_match.start()].strip()
            else:
                section_content = content[match.end():].strip()

            # Only add non-empty sections
            if section_key and section_content:
                sections[section_key] = section_content

        return sections

    def _claude_document_analysis(self, content, doc_type=None, basic_structure=None):
        """
        Use Claude to analyze the document and extract a structured representation

        Args:
            content (str): Raw document content
            doc_type (str, optional): Document type hint (if available)
            basic_structure (dict): Basic structure data already extracted

        Returns:
            dict: Structured content as organized by Claude, or None if analysis fails
        """
        try:
            # Prepare the prompt for Claude
            prompt = self._create_document_analysis_prompt(content, doc_type, basic_structure)

            # Make the API request
            response = self._call_claude_api(prompt)
            if not response:
                return None

            # Process the response
            structured_content = self._process_claude_response(response)
            if structured_content:
                return structured_content

            return None
        except Exception as e:
            self.logger.error(f"Error in Claude document analysis: {str(e)}")
            return None

    def _create_document_analysis_prompt(self, content, doc_type=None, basic_structure=None):
        """Create a prompt to analyze the document structure"""
        # Truncate content if it's too long (Claude has token limits)
        max_content_length = 10000  # Adjust based on Claude's limitations
        truncated_content = content
        if len(content) > max_content_length:
            truncated_content = content[:max_content_length] + "\n[... content truncated due to length ...]"

        # Create a prompt that will work reliably with Claude
        prompt = f"""
I need you to analyze a document and extract its structure in a consistent JSON format.

# Document to analyze:
```
{truncated_content}
```

# Instructions:
1. Identify the document type (e.g., PRD, strategy document, requirements doc, etc.)
2. Extract the main sections and their content
3. Organize the content into a clear hierarchical structure
4. Return ONLY a valid JSON object with the following structure:

{{
  "document_type": "The identified document type",
  "title": "The document's title",
  "summary": "A brief 1-2 sentence summary of the document",
  "sections": {{
    "section_name": "Section content",
    "another_section": {{
      "subsection": "Subsection content"
    }}
  }},
  "key_points": [
    "Key point 1",
    "Key point 2"
  ],
  "metadata": {{
    "estimated_type": "Your assessment of what kind of document this is",
    "primary_purpose": "What this document is used for",
    "target_audience": "Who the document is written for"
  }}
}}

Your response should be ONLY the JSON. No explanations before or after. No markdown formatting.
Keep the JSON structure clean and valid. Ensure all keys and values are properly quoted.
"""

        # If doc_type is provided, include it as a hint
        if doc_type:
            prompt += f"\nDocument type hint: {doc_type}"

        return prompt

    def _call_claude_api(self, prompt):
        """Make a direct call to the Claude API with improved error handling"""
        try:
            api_key = current_app.config.get('CLAUDE_API_KEY')
            model = current_app.config.get('CLAUDE_MODEL', 'claude-3-opus-20240229')

            if not api_key:
                self.logger.error("No Claude API key available")
                return None

            # Configure the request
            headers = {
                'anthropic-version': '2023-06-01',
                'x-api-key': api_key,
                'content-type': 'application/json'
            }

            data = {
                'model': model,
                'max_tokens': 3000,
                'messages': [
                    {'role': 'user', 'content': prompt}
                ]
            }

            # Make the request
            self.logger.info("Making request to Claude API")
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                json=data,
                timeout=30
            )

            # Check for successful response
            if response.status_code != 200:
                self.logger.error(f"Claude API error: {response.status_code} - {response.text}")
                return None

            return response.json()

        except Exception as e:
            self.logger.error(f"Error calling Claude API: {str(e)}")
            return None

    def _process_claude_response(self, response_data):
        """
        Process Claude's response into structured content

        Args:
            response_data (dict): The JSON response from Claude

        Returns:
            dict: Structured content or None if processing fails
        """
        try:
            # Extract text from the response
            if 'content' not in response_data or not isinstance(response_data['content'], list):
                self.logger.error("Unexpected response structure: 'content' missing or not a list")
                return None

            # Combine all text blocks
            response_text = ""
            for item in response_data['content']:
                if isinstance(item, dict) and item.get('type') == 'text':
                    response_text += item.get('text', '')

            if not response_text:
                self.logger.error("No text content found in response")
                return None

            # Try to find JSON in the response (Claude might sometimes add explanatory text)
            json_pattern = r'({[\s\S]*})'
            json_match = re.search(json_pattern, response_text)

            if not json_match:
                self.logger.error("No JSON object found in Claude response")
                return None

            json_text = json_match.group(1)

            # Parse the JSON
            try:
                structured_content = json.loads(json_text)
                return structured_content
            except json.JSONDecodeError as e:
                self.logger.error(f"Error parsing JSON from Claude: {str(e)}")

                # Try to clean up the JSON and parse again
                cleaned_json = json_text.replace('\n', ' ')
                cleaned_json = re.sub(r'\s+', ' ', cleaned_json)

                try:
                    structured_content = json.loads(cleaned_json)
                    return structured_content
                except json.JSONDecodeError:
                    self.logger.error("Failed to parse JSON even after cleaning")
                    return None

        except Exception as e:
            self.logger.error(f"Error processing Claude response: {str(e)}")
            return None