# services/artifacts/base_generator.py
import json
import logging
from flask import current_app
import anthropic
from abc import ABC, abstractmethod

class BaseGenerator(ABC):
    """
    Base class for all artifact generators.

    This abstract class provides common functionality for all artifact generators,
    including Claude API integration, error handling, and format standardization.
    """

    def __init__(self):
        """Initialize the generator with a logger."""
        self.logger = logging.getLogger(self.__class__.__name__)

    def generate_with_claude(self, prompt, fallback_method, fallback_args=None):
        """
        Generate content using Claude with proper error handling.

        Args:
            prompt (str): The prompt to send to Claude
            fallback_method (callable): Method to call if Claude fails
            fallback_args (dict, optional): Arguments to pass to fallback_method

        Returns:
            str: JSON string containing the generated content
        """
        if fallback_args is None:
            fallback_args = {}

        # Initialize Claude client
        try:
            api_key = current_app.config.get('CLAUDE_API_KEY')
            model = current_app.config.get('CLAUDE_MODEL', 'claude-3-opus-20240229')
            client = anthropic.Anthropic(api_key=api_key)
        except Exception as e:
            self.logger.error(f"Error initializing Claude client: {str(e)}")
            # Fall back to rule-based generation if Claude is unavailable
            return fallback_method(**fallback_args)

        try:
            # Call Claude
            response = client.messages.create(
                model=model,
                max_tokens=1500,
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
                try:
                    # Validate JSON by parsing it
                    result = json.loads(json_str)
                    return json.dumps(result)
                except json.JSONDecodeError as je:
                    self.logger.error(f"Invalid JSON in Claude response: {str(je)}")
                    return fallback_method(**fallback_args)
            else:
                self.logger.error("Could not find JSON in Claude response")
                return fallback_method(**fallback_args)

        except Exception as e:
            self.logger.error(f"Error generating content with Claude: {str(e)}")
            # Fall back to rule-based generation
            return fallback_method(**fallback_args)

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