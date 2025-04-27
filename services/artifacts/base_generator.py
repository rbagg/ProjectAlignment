# services/artifacts/base_generator.py
import json
import logging
import requests
import time
import re
from abc import ABC, abstractmethod
from flask import current_app

class BaseGenerator(ABC):
    """
    Base class for all artifact generators.

    This abstract class provides common functionality for all artifact generators,
    including Claude API integration, error handling, and format standardization.
    """

    def __init__(self):
        """Initialize the generator with a logger."""
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def generate(self, *args, **kwargs):
        """
        Generate content based on project data.

        This method must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def get_latest(self):
        """
        Get the latest generated content.

        This method must be implemented by subclasses.
        """
        pass

    def extract_json_from_text(self, text):
        """
        Extract JSON from Claude's response text.

        This method tries multiple approaches to find valid JSON in the text.

        Args:
            text (str): Response text that may contain JSON

        Returns:
            str: Valid JSON string if found, or None
        """
        # Try to find complete JSON array or object
        # First look for array pattern
        array_match = re.search(r'(\[\s*\{.*\}\s*\])', text, re.DOTALL)
        if array_match:
            try:
                json_str = array_match.group(1)
                # Validate by parsing it
                json.loads(json_str)
                return json_str
            except json.JSONDecodeError:
                self.logger.debug("Found array-like text but not valid JSON")

        # Try to find object pattern
        obj_match = re.search(r'(\{\s*".*"\s*:.*\})', text, re.DOTALL)
        if obj_match:
            try:
                json_str = obj_match.group(1)
                # Validate by parsing it
                json.loads(json_str)
                return json_str
            except json.JSONDecodeError:
                self.logger.debug("Found object-like text but not valid JSON")

        # If direct regex didn't work, try to find JSON between triple backticks
        code_block_match = re.search(r'```(?:json)?\s*(.+?)```', text, re.DOTALL)
        if code_block_match:
            try:
                json_str = code_block_match.group(1).strip()
                # Validate by parsing it
                json.loads(json_str)
                return json_str
            except json.JSONDecodeError:
                self.logger.debug("Found code block but not valid JSON")

        # As a last resort, try a more complex approach by scanning for JSON start/end brackets
        try:
            # Find potential JSON start positions
            start_positions = []
            for i, char in enumerate(text):
                if char in ['{', '[']:
                    start_positions.append(i)

            # Try each starting position
            for start_pos in start_positions:
                # Based on whether it starts with { or [, look for matching end
                is_object = text[start_pos] == '{'
                stack = [text[start_pos]]
                in_string = False
                escape_next = False

                for i in range(start_pos + 1, len(text)):
                    char = text[i]

                    # Handle escape sequences
                    if escape_next:
                        escape_next = False
                        continue
                    if char == '\\':
                        escape_next = True
                        continue

                    # Handle string literals
                    if char == '"' and not escape_next:
                        in_string = not in_string
                        continue

                    # Only process brackets outside of strings
                    if not in_string:
                        if char == '{' or char == '[':
                            stack.append(char)
                        elif char == '}' and stack and stack[-1] == '{':
                            stack.pop()
                            if not stack:  # Found complete JSON object
                                json_str = text[start_pos:i+1]
                                try:
                                    json.loads(json_str)
                                    return json_str
                                except json.JSONDecodeError:
                                    break  # Invalid JSON, try next starting position
                        elif char == ']' and stack and stack[-1] == '[':
                            stack.pop()
                            if not stack:  # Found complete JSON array
                                json_str = text[start_pos:i+1]
                                try:
                                    json.loads(json_str)
                                    return json_str
                                except json.JSONDecodeError:
                                    break  # Invalid JSON, try next starting position
        except Exception as e:
            self.logger.error(f"Error in complex JSON extraction: {str(e)}")

        self.logger.error("Could not extract valid JSON from text")
        return None

    def generate_with_claude_direct(self, prompt, fallback_method, fallback_args=None):
        """
        Generate content using Claude API directly with requests instead of the SDK.

        Args:
            prompt (str): The prompt to send to Claude
            fallback_method (callable): Method to call if Claude fails
            fallback_args (dict, optional): Arguments to pass to fallback_method

        Returns:
            str: JSON string containing the generated content
        """
        if fallback_args is None:
            fallback_args = {}

        # Get configuration
        try:
            api_key = current_app.config.get('CLAUDE_API_KEY')
            model = current_app.config.get('CLAUDE_MODEL', 'claude-3-opus-20240229')

            if not api_key:
                self.logger.error("No Claude API key found in configuration")
                return fallback_method(**fallback_args)

        except Exception as e:
            self.logger.error(f"Error accessing configuration: {str(e)}")
            return fallback_method(**fallback_args)

        # Add clear instructions for JSON output and no made-up statistics
        enhanced_prompt = f"""
{prompt}

IMPORTANT:
1. Respond ONLY with valid JSON. Do not include any explanatory text before or after the JSON.
2. Do not make up any statistics or percentages. If you don't have real data, describe impacts in qualitative terms.
3. The JSON should be properly formatted with no trailing commas or syntax errors.
"""

        # Setup request parameters
        max_retries = 3
        retry_delay = 2  # seconds

        # Try to call Claude API
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    self.logger.info(f"Retrying Claude API call (attempt {attempt + 1}/{max_retries}) after {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff

                response = requests.post(
                    'https://api.anthropic.com/v1/messages',
                    json={
                        'model': model,
                        'max_tokens': 1500,
                        'messages': [{'role': 'user', 'content': enhanced_prompt}]
                    },
                    headers={
                        'x-api-key': api_key,
                        'anthropic-version': '2023-06-01',
                        'Content-Type': 'application/json'
                    },
                    timeout=30  # 30 second timeout
                )

                # Check for successful response
                if response.status_code == 200:
                    response_data = response.json()
                    response_text = response_data.get('content', [{}])[0].get('text', '')

                    # Try to parse as JSON directly first
                    try:
                        json_obj = json.loads(response_text)
                        return json.dumps(json_obj)
                    except json.JSONDecodeError:
                        # If not valid JSON, try to extract JSON from the text
                        json_str = self.extract_json_from_text(response_text)
                        if json_str:
                            return json_str
                        else:
                            self.logger.error("Could not find valid JSON in Claude response")
                            if attempt == max_retries - 1:
                                return fallback_method(**fallback_args)
                else:
                    self.logger.error(f"Error from Claude API: {response.status_code} - {response.text}")
                    if attempt == max_retries - 1:
                        return fallback_method(**fallback_args)

            except Exception as e:
                self.logger.error(f"Error calling Claude API: {str(e)}")
                if attempt == max_retries - 1:
                    return fallback_method(**fallback_args)

        # If we get here, all attempts failed
        return fallback_method(**fallback_args)

    def generate_with_claude(self, prompt, fallback_method, fallback_args=None):
        """
        Generate content using Claude with proper error handling.

        This method is maintained for backward compatibility but now uses
        the direct API approach instead of the SDK.

        Args:
            prompt (str): The prompt to send to Claude
            fallback_method (callable): Method to call if Claude fails
            fallback_args (dict, optional): Arguments to pass to fallback_method

        Returns:
            str: JSON string containing the generated content
        """
        return self.generate_with_claude_direct(prompt, fallback_method, fallback_args)

    def parse_content(self, content_json):
        """
        Safely parse JSON content with error handling.

        Args:
            content_json (str): JSON string to parse

        Returns:
            dict: Parsed content or empty dict if parsing fails
        """
        try:
            return json.loads(content_json)
        except (json.JSONDecodeError, TypeError) as e:
            self.logger.error(f"Error parsing content: {str(e)}")
            return {}

    def format_prompt(self, role, context, task, format_guidelines, process, content_req, 
                      constraints, examples=None, interaction=None, quality=None):
        """
        Format a prompt according to the master prompt structure.

        Args:
            role (str): Role definition for Claude
            context (str): Context and background information
            task (str): Task definition and objectives
            format_guidelines (str): Format and structure guidelines
            process (str): Process instructions
            content_req (str): Content requirements
            constraints (str): Constraints and limitations
            examples (str, optional): Examples and references
            interaction (str, optional): Interaction guidelines
            quality (str, optional): Quality assurance criteria

        Returns:
            str: Formatted prompt following master structure
        """
        # Add standard instructions about JSON and avoiding fake statistics to all prompts
        standard_instructions = """
VERY IMPORTANT INSTRUCTIONS:
1. Provide ONLY valid JSON in your response. Do not include any explanatory text, instructions, or commentary.
2. Do not make up statistics, percentages, or metrics. If you don't have real data, use qualitative descriptions instead.
3. The JSON must be properly formatted with no trailing commas, unescaped quotes, or other syntax errors.
4. Your response will be parsed directly as JSON, so it must strictly adhere to JSON syntax.
"""

        prompt_parts = [
            f"# 1. Role & Identity Definition\n{role}",
            f"# 2. Context & Background\n{context}",
            f"# 3. Task Definition & Objectives\n{task}",
            f"# 4. Format & Structure Guidelines\n{format_guidelines}",
            f"# 5. Process Instructions\n{process}",
            f"# 6. Content Requirements\n{content_req}",
            f"# 7. Constraints & Limitations\n{constraints}"
        ]

        if examples:
            prompt_parts.append(f"# 8. Examples & References\n{examples}")

        if interaction:
            prompt_parts.append(f"# 9. Interaction Guidelines\n{interaction}")

        if quality:
            prompt_parts.append(f"# 10. Quality Assurance\n{quality}")

        prompt_parts.append(f"# 11. Special Instructions\n{standard_instructions}")

        return "\n\n".join(prompt_parts)