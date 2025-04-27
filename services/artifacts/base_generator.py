# services/artifacts/base_generator.py
import json
import logging
import requests
import time
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
                        'messages': [{'role': 'user', 'content': prompt}]
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

                    print(response_text)

                    # More robust JSON extraction using regex
                    import re

                    # Try to find JSON object first
                    json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                    else:
                        # Try to find JSON array if no object found
                        json_match = re.search(r'(\[.*\])', response_text, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(1)
                        else:
                            self.logger.error("Could not find JSON in Claude response")
                            if attempt == max_retries - 1:
                                return fallback_method(**fallback_args)
                            continue

                    try:
                        # Try to parse the JSON
                        parsed = json.loads(json_str)
                        return json.dumps(parsed)
                    except json.JSONDecodeError as je:
                        self.logger.error(f"Invalid JSON in Claude response: {str(je)}")

                        # Try a more aggressive approach - find just the first valid JSON block
                        try:
                            # Log the response for debugging
                            self.logger.debug(f"Response text: {response_text[:500]}")

                            # Try to extract JSON more carefully
                            for i, char in enumerate(response_text):
                                if char in ['{', '[']:
                                    # Found potential start of JSON
                                    try:
                                        # Try to parse from here to end
                                        partial = response_text[i:]
                                        # Count opening and closing brackets to find matching end
                                        stack = []
                                        in_string = False
                                        escape_next = False

                                        for j, c in enumerate(partial):
                                            if escape_next:
                                                escape_next = False
                                                continue

                                            if c == '\\':
                                                escape_next = True
                                                continue

                                            if c == '"' and not escape_next:
                                                in_string = not in_string
                                                continue

                                            if not in_string:
                                                if c in ['{', '[']:
                                                    stack.append(c)
                                                elif c == '}' and stack and stack[-1] == '{':
                                                    stack.pop()
                                                    if not stack:
                                                        # Found matching end
                                                        json_str = partial[:j+1]
                                                        parsed = json.loads(json_str)
                                                        return json.dumps(parsed)
                                                elif c == ']' and stack and stack[-1] == '[':
                                                    stack.pop()
                                                    if not stack:
                                                        # Found matching end
                                                        json_str = partial[:j+1]
                                                        parsed = json.loads(json_str)
                                                        return json.dumps(parsed)
                                    except Exception as je2:
                                        # Keep trying
                                        continue

                            # If we get here, we couldn't find valid JSON
                            if attempt == max_retries - 1:
                                return fallback_method(**fallback_args)
                        except Exception as e2:
                            self.logger.error(f"Error in aggressive JSON extraction: {str(e2)}")
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

        return "\n\n".join(prompt_parts)