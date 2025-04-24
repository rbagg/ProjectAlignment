import json
import os
import sys
import re
import requests
import argparse

# Import prompts
try:
    from prompts import get_prompt
except ImportError:
    print("Prompts file not found. Make sure prompts.py is in the same directory.")
    sys.exit(1)

# Simple mock for the Project model
class MockProject:
    def __init__(self, content=None, description=None, internal_messaging=None, external_messaging=None):
        self.content = content
        self.description = description
        self.internal_messaging = internal_messaging
        self.external_messaging = external_messaging

# Simple mock for the current_app configuration
class MockApp:
    config = {
        'CLAUDE_API_KEY': os.environ.get('CLAUDE_API_KEY', ''),
        'CLAUDE_MODEL': 'claude-3-opus-20240229'
    }

# Mock the flask current_app
sys.modules['flask'] = type('MockFlask', (), {'current_app': MockApp})

# Mock the models
sys.modules['models'] = type('MockModels', (), {'Project': MockProject})

def call_claude_api(prompt):
    """Call Claude API directly using HTTP requests"""
    api_key = os.environ.get('CLAUDE_API_KEY')
    if not api_key:
        return None

    headers = {
        'x-api-key': api_key,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json'
    }

    data = {
        'model': 'claude-3-opus-20240229',
        'max_tokens': 1500,  # Increased max tokens to ensure full response with objections
        'messages': [
            {'role': 'user', 'content': prompt}
        ]
    }

    try:
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers=headers,
            json=data
        )
        response.raise_for_status()
        result = response.json()
        return result['content'][0]['text']
    except Exception as e:
        print(f"Error calling Claude API: {e}")
        return None

def clean_bullets_and_lists(text):
    """Clean bullet points and numbered lists from text"""
    if not text:
        return ""

    # Clean bullet points
    text = re.sub(r'(?m)^\s*[\*\-•]\s*', '', text)

    # Clean numbered lists
    text = re.sub(r'(?m)^\s*\d+\.\s*', '', text)

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)

    return text.strip()

def extract_first_sentence(text):
    """Extract just the first complete sentence from text"""
    if not text:
        return ""

    # Remove any markdown or formatting
    text = clean_markdown_text(text)
    text = clean_bullets_and_lists(text)

    # Find the first sentence
    sentence_match = re.search(r'^([^.!?]+[.!?])', text)
    if sentence_match:
        return sentence_match.group(1).strip()

    # If no complete sentence, return up to 100 chars
    if len(text) > 100:
        return text[:100].strip() + "..."

    return text.strip()

def extract_sections_from_readme(content):
    """Extract sections from README content using more robust parsing"""
    # Get project name (first heading)
    project_name = "Project Alignment Tool"
    title_match = re.search(r'^#\s+(.+?)$', content, re.MULTILINE)
    if title_match:
        project_name = title_match.group(1).strip()

    # Extract sections based on markdown headers
    sections = {}

    # Try to find the Overview/Introduction section
    overview = ""
    overview_pattern = re.search(r'(?:^|\n)##\s*(?:Overview|Introduction)\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL | re.MULTILINE)
    if overview_pattern:
        overview = overview_pattern.group(1).strip()
    else:
        # If no Overview section, try to get the first paragraph after the title
        first_para = re.search(r'^#\s+.+?\n\n(.*?)(?=\n\n|\Z)', content, re.DOTALL | re.MULTILINE)
        if first_para:
            overview = first_para.group(1).strip()
    sections['overview'] = overview

    # Find Pain Points or Challenges section
    pain_points = ""
    pain_pattern = re.search(r'(?:^|\n)##\s*(?:Pain Points|Challenges|Problems)\s*(?:Addressed)?\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL | re.MULTILINE)
    if pain_pattern:
        pain_points = pain_pattern.group(1).strip()
    sections['pain_points'] = pain_points

    # Find Solution section
    solution = ""
    solution_pattern = re.search(r'(?:^|\n)##\s*(?:Solution|Approach|How It Works)\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL | re.MULTILINE)
    if solution_pattern:
        solution = solution_pattern.group(1).strip()
    sections['solution'] = solution

    # Find Benefits/Features section
    benefits = ""
    benefits_pattern = re.search(r'(?:^|\n)##\s*(?:Key Benefits|Benefits|Features|Key Features)\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL | re.MULTILINE)
    if benefits_pattern:
        benefits = benefits_pattern.group(1).strip()
    sections['benefits'] = benefits

    # Clean markdown formatting from each section
    cleaned_sections = {}
    for key, value in sections.items():
        # Clean markdown formatting first
        cleaned = clean_markdown_text(value)

        # Store both the full cleaned text
        cleaned_sections[key] = cleaned

    return project_name, cleaned_sections

def clean_markdown_text(text):
    """Clean markdown formatting from text"""
    if not text:
        return ""

    # Remove markdown headers
    text = re.sub(r'^#{1,6}\s+.*$', '', text, flags=re.MULTILINE)

    # Remove markdown list markers
    text = re.sub(r'^\s*[\*\-\+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

    # Remove markdown emphasis
    text = re.sub(r'[*_]{1,2}(.*?)[*_]{1,2}', r'\1', text)

    # Remove markdown code blocks and inline code
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'`(.*?)`', r'\1', text)

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove leading/trailing whitespace
    text = text.strip()

    return text

def direct_generate_with_claude(sections, project_name):
    """Generate artifacts directly using Claude API via HTTP with MOO prompts"""
    # Create context for Claude
    context = f"""
Project Name: {project_name}

Overview:
{sections['overview']}

Pain Points:
{sections['pain_points']}

Solution:
{sections['solution']}

Benefits:
{sections['benefits']}
    """

    # Always use the standard prompt types (which are now MOO-integrated)
    desc_prompt_type = 'project_description'
    internal_prompt_type = 'internal_messaging'
    external_prompt_type = 'external_messaging'

    # Get prompts with context and variables filled in
    desc_prompt = get_prompt(desc_prompt_type, context)
    internal_prompt = get_prompt(internal_prompt_type, context, project_name=project_name)
    external_prompt = get_prompt(external_prompt_type, context)

    # Call Claude API for each prompt
    print("Calling Claude API for project description...")
    desc_text = call_claude_api(desc_prompt)

    print("Calling Claude API for internal messaging...")
    internal_text = call_claude_api(internal_prompt)

    print("Calling Claude API for external messaging...")
    external_text = call_claude_api(external_prompt)

    # Extract JSON from responses
    desc_json = extract_json(desc_text) if desc_text else None
    internal_json = extract_json(internal_text) if internal_text else None
    external_json = extract_json(external_text) if external_text else None

    return desc_json, internal_json, external_json

def extract_json(text):
    """Extract JSON from Claude's response"""
    if not text:
        print("Empty response received from Claude API")
        return None

    json_start = text.find('{')
    json_end = text.rfind('}') + 1

    if json_start != -1 and json_end != -1:
        json_str = text[json_start:json_end]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from Claude response: {e}")
            print(f"Extracted text: {json_str[:200]}...")  # Show just the start to avoid cluttering output
            # In case of complex formats, try more robust extraction
            try:
                # Find where the JSON object seems to start and end
                bracketing = 0
                real_end = 0
                for i, char in enumerate(text[json_start:]):
                    if char == '{':
                        bracketing += 1
                    elif char == '}':
                        bracketing -= 1
                        if bracketing == 0:
                            real_end = json_start + i + 1
                            break

                if real_end > 0:
                    better_json_str = text[json_start:real_end]
                    return json.loads(better_json_str)
            except:
                pass  # If that didn't work either, just return None

    print("No valid JSON found in Claude's response")
    print("Response starts with:", text[:200] + "..." if len(text) > 200 else text)
    return None

def print_objections(objections, title="Objections"):
    """Print objections and responses in a readable format"""
    if not objections or not isinstance(objections, list):
        print(f"\n{title}: None found in response")
        return

    print(f"\n{title}:")
    for i, obj in enumerate(objections):
        if isinstance(obj, dict):
            print(f"\nObjection {i+1}: {obj.get('objection', '')}")
            print(f"Response: {obj.get('response', '')}")

def test_with_readme(readme_path):
    """Test the artifact generators with a README file"""
    try:
        # Read the README file
        with open(readme_path, 'r') as f:
            readme_content = f.read()

        # Extract sections from the README
        project_name, sections = extract_sections_from_readme(readme_content)

        # Print diagnostic info first
        print("\n========== EXTRACTED CONTENT ==========")
        print(f"Project Name: {project_name}")

        for section_name, content in sections.items():
            print(f"\n{section_name.title()}:")
            # Print just the first 200 chars if it's long
            if len(content) > 200:
                print(content[:200] + "...")
            else:
                print(content)

        # Check if Claude API key is available
        api_key = os.environ.get('CLAUDE_API_KEY')
        if api_key:
            print(f"\nClaude API key is available! Generating content directly with Claude...")
            print("Using MOO-integrated prompts for generation (objections will be included)")

            # Try to generate content directly with Claude
            desc_json, internal_json, external_json = direct_generate_with_claude(sections, project_name)

            if desc_json and internal_json and external_json:
                # Print Claude-generated results
                print("\n========== CLAUDE-GENERATED PROJECT DESCRIPTION ==========")
                print("\nThree Sentences:")
                for i, sentence in enumerate(desc_json['three_sentences']):
                    print(f"{i+1}. {sentence}")

                print("\nThree Paragraphs:")
                for i, paragraph in enumerate(desc_json['three_paragraphs']):
                    print(f"\nParagraph {i+1}:")
                    print(paragraph)

                # Print objections
                if 'objections' in desc_json:
                    print_objections(desc_json['objections'])
                else:
                    print("\nWARNING: No objections found in project description response!")

                print("\n\n========== CLAUDE-GENERATED INTERNAL MESSAGING ==========")
                print(f"\nSubject: {internal_json.get('subject', '')}")
                print(f"\nWhat It Is: {internal_json.get('what_it_is', '')}")
                print(f"\nCustomer Pain: {internal_json.get('customer_pain', '')}")
                print(f"\nOur Solution: {internal_json.get('our_solution', '')}")
                print(f"\nBusiness Impact: {internal_json.get('business_impact', '')}")

                # Print objections
                if 'objections' in internal_json:
                    print_objections(internal_json['objections'])
                else:
                    print("\nWARNING: No objections found in internal messaging response!")

                print("\n\n========== CLAUDE-GENERATED EXTERNAL MESSAGING ==========")
                print(f"\nHeadline: {external_json.get('headline', '')}")
                print(f"\nPain Point: {external_json.get('pain_point', '')}")
                print(f"\nSolution: {external_json.get('solution', '')}")
                print(f"\nBenefits: {external_json.get('benefits', '')}")
                if 'call_to_action' in external_json:
                    print(f"\nCall to Action: {external_json.get('call_to_action', '')}")

                # Print objections
                if 'objections' in external_json:
                    print_objections(external_json['objections'])
                else:
                    print("\nWARNING: No objections found in external messaging response!")

                return True
            else:
                print("Claude API returned incomplete results. Falling back to rule-based generation.")
        else:
            print("\nNOTE: Claude API key not found. Using rule-based generation.")

        # Import generators for rule-based generation
        print("\nFalling back to rule-based generators...")
        from services.artifacts.project_description import ProjectDescriptionGenerator
        from services.artifacts.internal_messaging import InternalMessagingGenerator
        from services.artifacts.external_messaging import ExternalMessagingGenerator

        # Create better formatted content with more concise sections
        better_content = {
            'prd': {
                'name': project_name,
                'overview': extract_first_sentence(sections['overview']),
                'problem_statement': extract_first_sentence(sections['pain_points']),
                'solution': extract_first_sentence(sections['solution'])
            },
            'tickets': [],
            'strategy': {
                'vision': extract_first_sentence(sections['overview']),
                'business_value': extract_first_sentence(sections['benefits'])
            },
            'prfaq': {
                'frequently_asked_questions': [
                    {
                        'question': 'What problem does this solve?',
                        'answer': extract_first_sentence(sections['pain_points'])
                    },
                    {
                        'question': 'What are the benefits?',
                        'answer': extract_first_sentence(sections['benefits'])
                    }
                ]
            }
        }

        # Convert to JSON
        project_content = json.dumps(better_content)

        # Initialize generators
        project_desc_gen = ProjectDescriptionGenerator()
        internal_msg_gen = InternalMessagingGenerator()
        external_msg_gen = ExternalMessagingGenerator()

        # Generate artifacts
        description = project_desc_gen.generate(project_content)
        internal_msg = internal_msg_gen.generate(project_content)
        external_msg = external_msg_gen.generate(project_content)

        # Print results
        print("\n========== RULE-BASED PROJECT DESCRIPTION ==========")
        description_obj = json.loads(description)

        print("\nThree Sentences:")
        for i, sentence in enumerate(description_obj['three_sentences']):
            print(f"{i+1}. {sentence}")

        print("\nThree Paragraphs:")
        for i, paragraph in enumerate(description_obj['three_paragraphs']):
            print(f"\nParagraph {i+1}:")
            print(paragraph)

        # Print objections if present
        if 'objections' in description_obj:
            print_objections(description_obj['objections'])
        else:
            print("\nWARNING: No objections found in rule-based project description!")

        print("\n\n========== RULE-BASED INTERNAL MESSAGING ==========")
        internal_obj = json.loads(internal_msg)

        print(f"\nSubject: {internal_obj.get('subject', '')}")
        print(f"\nWhat It Is: {internal_obj.get('what_it_is', '')}")
        print(f"\nCustomer Pain: {internal_obj.get('customer_pain', '')}")
        print(f"\nOur Solution: {internal_obj.get('our_solution', '')}")
        print(f"\nBusiness Impact: {internal_obj.get('business_impact', '')}")

        # Print objections if present
        if 'objections' in internal_obj:
            print_objections(internal_obj['objections'])
        else:
            print("\nWARNING: No objections found in rule-based internal messaging!")

        print("\n\n========== RULE-BASED EXTERNAL MESSAGING ==========")
        external_obj = json.loads(external_msg)

        print(f"\nHeadline: {external_obj.get('headline', '')}")
        print(f"\nPain Point: {external_obj.get('pain_point', '')}")
        print(f"\nSolution: {external_obj.get('solution', '')}")
        print(f"\nBenefits: {external_obj.get('benefits', '')}")
        if 'call_to_action' in external_obj:
            print(f"\nCall to Action: {external_obj.get('call_to_action', '')}")

        # Print objections if present
        if 'objections' in external_obj:
            print_objections(external_obj['objections'])
        else:
            print("\nWARNING: No objections found in rule-based external messaging!")

        return True

    except Exception as e:
        print(f"Error testing with README: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test artifact generators with a README file')
    parser.add_argument('readme_path', help='Path to the README file')

    args = parser.parse_args()

    if not os.path.exists(args.readme_path):
        print(f"Error: File {args.readme_path} does not exist")
        sys.exit(1)

    success = test_with_readme(args.readme_path)

    if success:
        print("\nTest completed successfully!")
    else:
        print("\nTest failed.")
        sys.exit(1)