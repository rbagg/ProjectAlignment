#!/usr/bin/env python3
"""
Test script for the Project Alignment Tool.
This demonstrates how to use the generators, objection system, and improvement system.
"""

import json
import os
import sys
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up Flask application context for testing
from flask import Flask, current_app
from config import Config

# Import models and services
from models import db, Project
from services.artifacts.project_description import ProjectDescriptionGenerator
from services.artifacts.internal_messaging import InternalMessagingGenerator
from services.artifacts.external_messaging import ExternalMessagingGenerator
from services.artifacts.objection_generator import ObjectionGenerator
from services.artifacts.improvement_generator import ImprovementGenerator

# Try to get the Claude API key from Replit secrets
claude_api_key = os.environ.get('CLAUDE_API_KEY')

# Setup test environment with API key if available
app = Flask(__name__)
config = Config()

if claude_api_key:
    # If found directly in environment, use it
    config.CLAUDE_API_KEY = claude_api_key
    app.config['CLAUDE_API_KEY'] = claude_api_key
    print("Found Claude API key in environment variables!")
else:
    print("WARNING: No Claude API key found in environment variables.")
    print("Will check application config during execution.")

# Configure Flask application
app.config.from_object(config)
db.init_app(app)

# Test project content (simplified example)
TEST_PROJECT = {
    'prd': {
        'name': 'Document Sync Tool',
        'overview': 'A tool that synchronizes documentation across different systems and keeps everything in alignment.',
        'problem_statement': 'Teams waste hours reconciling inconsistent documentation across different systems, leading to errors and delays.',
        'solution': 'We automatically monitor document changes and suggest updates to maintain alignment across all connected documents.'
    },
    'prfaq': {
        'press_release': 'Announcing Document Sync Tool: End the document alignment nightmare once and for all.',
        'frequently_asked_questions': [
            {
                'question': 'What problem does this solve?',
                'answer': 'Teams waste 4+ hours weekly reconciling inconsistent documentation.'
            },
            {
                'question': 'How does it work?',
                'answer': 'We connect to your documentation systems and monitor changes, then suggest updates to maintain alignment.'
            }
        ]
    },
    'strategy': {
        'vision': 'Create a world where documentation is always accurate and teams never waste time on reconciliation.',
        'approach': 'Build connectors to popular documentation systems and use NLP to identify inconsistencies.',
        'business_value': 'Save teams 4+ hours per week and reduce implementation errors by 45%.'
    },
    'tickets': [
        {
            'id': 'SYNC-1',
            'title': 'Implement document connector system',
            'status': 'In Progress'
        },
        {
            'id': 'SYNC-2',
            'title': 'Build inconsistency detection engine',
            'status': 'To Do'
        },
        {
            'id': 'SYNC-3',
            'title': 'Create update suggestion system',
            'status': 'To Do'
        }
    ]
}

def print_section(title):
    """Print a section divider with title."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def pretty_print_json(data):
    """Pretty-print JSON data."""
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            print(data)
            return

    print(json.dumps(data, indent=2))

def check_api_key():
    """Check if API key is available in current app config."""
    with app.app_context():
        api_key = current_app.config.get('CLAUDE_API_KEY')
        if api_key:
            print("API key found in application config!")
            return True
        else:
            print("No API key found in application config.")
            print("Fallback methods will be used instead of Claude API.")
            return False

def test_project_description():
    """Test project description generation."""
    print_section("TESTING PROJECT DESCRIPTION GENERATOR")

    # Initialize generator
    print("Initializing ProjectDescriptionGenerator...")
    generator = ProjectDescriptionGenerator()

    # Generate description with objections and improvements
    print("Generating project description, objections, and improvements...")
    project_content = json.dumps(TEST_PROJECT)

    # Check API key and execute within app context
    with app.app_context():
        # Check if API key is available
        key_available = current_app.config.get('CLAUDE_API_KEY') is not None
        if key_available:
            print("Using Claude API for generation")
        else:
            print("Using fallback methods (API key not available)")

        # Generate content
        description_json = generator.generate(project_content)

    # Parse and display results
    description = json.loads(description_json)

    print("\nTHREE SENTENCES:")
    for i, sentence in enumerate(description["three_sentences"], 1):
        print(f"{i}. {sentence}")

    print("\nTHREE PARAGRAPHS:")
    for i, paragraph in enumerate(description["three_paragraphs"], 1):
        print(f"Paragraph {i}: {paragraph}")

    print("\nOBJECTIONS:")
    for objection in description.get("objections", []):
        print(f"- {objection['title']}: {objection['explanation']}")
        if "impact" in objection:
            print(f"  Impact: {objection['impact']}")

    print("\nIMPROVEMENTS:")
    for improvement in description.get("improvements", []):
        print(f"- {improvement['title']}: {improvement['suggestion']}")
        if "benefit" in improvement:
            print(f"  Benefit: {improvement['benefit']}")

def test_internal_messaging():
    """Test internal messaging generation."""
    print_section("TESTING INTERNAL MESSAGING GENERATOR")

    # Initialize generator
    print("Initializing InternalMessagingGenerator...")
    generator = InternalMessagingGenerator()

    # Generate messaging with objections and improvements
    print("Generating internal messaging, objections, and improvements...")
    project_content = json.dumps(TEST_PROJECT)

    # Execute within app context
    with app.app_context():
        # Check if API key is available
        key_available = current_app.config.get('CLAUDE_API_KEY') is not None
        if key_available:
            print("Using Claude API for generation")
        else:
            print("Using fallback methods (API key not available)")

        # Generate content
        messaging_json = generator.generate(project_content)

    # Parse and display results
    messaging = json.loads(messaging_json)

    print("\nINTERNAL MESSAGING:")
    print(f"Subject: {messaging.get('subject', '')}")
    print(f"What It Is: {messaging.get('what_it_is', '')}")
    print(f"Customer Pain: {messaging.get('customer_pain', '')}")
    print(f"Our Solution: {messaging.get('our_solution', '')}")
    print(f"Business Impact: {messaging.get('business_impact', '')}")

    if 'timeline' in messaging:
        print(f"Timeline: {messaging['timeline']}")

    if 'team_needs' in messaging:
        print(f"Team Needs: {messaging['team_needs']}")

    print("\nOBJECTIONS:")
    for objection in messaging.get("objections", []):
        print(f"- {objection['title']}: {objection['explanation']}")
        if "impact" in objection:
            print(f"  Impact: {objection['impact']}")

    print("\nIMPROVEMENTS:")
    for improvement in messaging.get("improvements", []):
        print(f"- {improvement['title']}: {improvement['suggestion']}")
        if "benefit" in improvement:
            print(f"  Benefit: {improvement['benefit']}")

def test_external_messaging():
    """Test external messaging generation."""
    print_section("TESTING EXTERNAL MESSAGING GENERATOR")

    # Initialize generator
    print("Initializing ExternalMessagingGenerator...")
    generator = ExternalMessagingGenerator()

    # Generate messaging with objections and improvements
    print("Generating external messaging, objections, and improvements...")
    project_content = json.dumps(TEST_PROJECT)

    # Execute within app context
    with app.app_context():
        # Check if API key is available
        key_available = current_app.config.get('CLAUDE_API_KEY') is not None
        if key_available:
            print("Using Claude API for generation")
        else:
            print("Using fallback methods (API key not available)")

        # Generate content
        messaging_json = generator.generate(project_content)

    # Parse and display results
    messaging = json.loads(messaging_json)

    print("\nEXTERNAL MESSAGING:")
    print(f"Headline: {messaging.get('headline', '')}")
    print(f"Pain Point: {messaging.get('pain_point', '')}")
    print(f"Solution: {messaging.get('solution', '')}")

    if 'benefits' in messaging:
        print(f"Benefits: {messaging['benefits']}")

    print(f"Call to Action: {messaging.get('call_to_action', '')}")

    print("\nOBJECTIONS:")
    for objection in messaging.get("objections", []):
        print(f"- {objection['title']}: {objection['explanation']}")
        if "impact" in objection:
            print(f"  Impact: {objection['impact']}")

    print("\nIMPROVEMENTS:")
    for improvement in messaging.get("improvements", []):
        print(f"- {improvement['title']}: {improvement['suggestion']}")
        if "benefit" in improvement:
            print(f"  Benefit: {improvement['benefit']}")

def test_direct_objection_generation():
    """Test direct objection generation."""
    print_section("TESTING DIRECT OBJECTION GENERATION")

    # Initialize generator
    print("Initializing ObjectionGenerator...")
    generator = ObjectionGenerator()

    # Generate objections directly
    print("Generating objections directly...")
    project_content = json.dumps(TEST_PROJECT)

    # Create a mock artifact
    mock_artifact = {
        "headline": "Save 4+ hours per week on documentation",
        "description": "Our tool automatically syncs your documents and keeps everything aligned."
    }

    # Execute within app context
    with app.app_context():
        # Check if API key is available
        key_available = current_app.config.get('CLAUDE_API_KEY') is not None
        if key_available:
            print("Using Claude API for generation")
        else:
            print("Using fallback methods (API key not available)")

        # Generate objections
        objections_json = generator.generate_for_artifact(
            json.loads(project_content), 
            mock_artifact, 
            'external'
        )

    # Parse and display results
    objections = json.loads(objections_json)

    print("\nDIRECTLY GENERATED OBJECTIONS:")
    for objection in objections:
        print(f"- {objection['title']}: {objection['explanation']}")
        if "impact" in objection:
            print(f"  Impact: {objection['impact']}")

def test_direct_improvement_generation():
    """Test direct improvement generation."""
    print_section("TESTING DIRECT IMPROVEMENT GENERATION")

    # Initialize generator
    print("Initializing ImprovementGenerator...")
    generator = ImprovementGenerator()

    # Generate improvements directly
    print("Generating improvements directly...")
    project_content = json.dumps(TEST_PROJECT)

    # Create a mock artifact
    mock_artifact = {
        "headline": "Save 4+ hours per week on documentation",
        "description": "Our tool automatically syncs your documents and keeps everything aligned."
    }

    # Execute within app context
    with app.app_context():
        # Check if API key is available
        key_available = current_app.config.get('CLAUDE_API_KEY') is not None
        if key_available:
            print("Using Claude API for generation")
        else:
            print("Using fallback methods (API key not available)")

        # Generate improvements
        improvements_json = generator.generate_for_artifact(
            json.loads(project_content), 
            mock_artifact, 
            'external'
        )

    # Parse and display results
    improvements = json.loads(improvements_json)

    print("\nDIRECTLY GENERATED IMPROVEMENTS:")
    for improvement in improvements:
        print(f"- {improvement['title']}: {improvement['suggestion']}")
        if "benefit" in improvement:
            print(f"  Benefit: {improvement['benefit']}")

def test_file_processing(file_path):
    """Test processing a specific file."""
    print_section(f"TESTING FILE PROCESSING: {file_path}")

    # Check if file exists
    if not os.path.isfile(file_path):
        print(f"ERROR: File not found: {file_path}")
        return

    # Read file content
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            print(f"Successfully read file: {file_path}")
            print(f"File size: {len(content)} characters")
    except Exception as e:
        print(f"ERROR reading file: {str(e)}")
        return

    # Create mock project structure based on file content
    mock_project = {
        'prd': {
            'name': os.path.basename(file_path),
            'overview': content[:500] + ("..." if len(content) > 500 else ""),
            'problem_statement': "Extracted from file content",
            'solution': "Generated based on file analysis"
        },
        'strategy': {
            'vision': "Vision extracted from file content",
            'approach': "Approach based on file analysis",
            'business_value': "Business value determined from content"
        },
        'tickets': []
    }

    # Initialize generators
    desc_generator = ProjectDescriptionGenerator()
    internal_generator = InternalMessagingGenerator()
    external_generator = ExternalMessagingGenerator()

    # Generate artifacts with app context
    with app.app_context():
        # Check if API key is available
        key_available = current_app.config.get('CLAUDE_API_KEY') is not None
        if key_available:
            print("Using Claude API for generation")
        else:
            print("Using fallback methods (API key not available)")

        print("Generating artifacts from file content...")

        # Convert to JSON string
        project_content = json.dumps(mock_project)

        # Generate artifacts
        description = desc_generator.generate(project_content)
        internal_msg = internal_generator.generate(project_content)
        external_msg = external_generator.generate(project_content)

    # Display results
    print("\nGENERATED ARTIFACTS FROM FILE:")

    # Display description
    description_data = json.loads(description)
    print("\nPROJECT DESCRIPTION:")
    if "three_sentences" in description_data:
        for i, sentence in enumerate(description_data["three_sentences"], 1):
            print(f"{i}. {sentence}")

    # Display objections
    if "objections" in description_data:
        print("\nKEY OBJECTIONS:")
        for objection in description_data["objections"][:2]:  # Show only top 2
            print(f"- {objection['title']}: {objection['explanation']}")

    # Display improvements
    if "improvements" in description_data:
        print("\nTOP IMPROVEMENTS:")
        for improvement in description_data["improvements"][:2]:  # Show only top 2
            print(f"- {improvement['title']}: {improvement['suggestion']}")

    print("\nComplete analysis generated. Use main app for full details.")

if __name__ == "__main__":
    print("Project Alignment Tool Test Script")
    print("=================================")
    print("This script demonstrates the functionality of the Project Alignment Tool")
    print("including content generation, objections, and improvements.")

    # Check for API key
    api_key_available = check_api_key()
    if not api_key_available:
        print("\nTo use the Claude API, make sure your API key is:")
        print("1. In your Replit Secrets as 'CLAUDE_API_KEY'")
        print("2. Or set in your environment variables")
        print("3. Or defined in config.py")

    # Check for file argument
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        # Process specific file
        test_file_processing(sys.argv[1])
    else:
        # Execute standard tests
        try:
            test_project_description()
            test_internal_messaging()
            test_external_messaging()
            test_direct_objection_generation()
            test_direct_improvement_generation()

            # Only run database test if specified
            if len(sys.argv) > 1 and sys.argv[1] == '--with-db':
                with app.app_context():
                    test_save_to_database()

            # If no valid file was provided but arguments exist
            if len(sys.argv) > 1 and not os.path.isfile(sys.argv[1]) and sys.argv[1] != '--with-db':
                print(f"\nWARNING: Could not find file: {sys.argv[1]}")
                print("Usage: python test.py [file_to_analyze.md] [--with-db]")

        except Exception as e:
            print(f"\nERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    print("\nAll tests completed!")