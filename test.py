#!/usr/bin/env python3
"""
Test script for the Project Alignment Tool.
This demonstrates how to use the generators, objection system, and improvement system.
"""

import json
import os
import sys
from datetime import datetime

# Set up Flask application context for testing
from flask import Flask
from config import Config

# Import models and services
from models import db, Project
from services.artifacts.project_description import ProjectDescriptionGenerator
from services.artifacts.internal_messaging import InternalMessagingGenerator
from services.artifacts.external_messaging import ExternalMessagingGenerator
from services.artifacts.objection_generator import ObjectionGenerator
from services.artifacts.improvement_generator import ImprovementGenerator

# Setup test environment
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Mock API key for testing - replace with your actual API key
os.environ['CLAUDE_API_KEY'] = 'your_api_key_here'  

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

def test_project_description():
    """Test project description generation."""
    print_section("TESTING PROJECT DESCRIPTION GENERATOR")

    # Initialize generator
    print("Initializing ProjectDescriptionGenerator...")
    generator = ProjectDescriptionGenerator()

    # Generate description with objections and improvements
    print("Generating project description, objections, and improvements...")
    project_content = json.dumps(TEST_PROJECT)
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

    # Generate objections for the mock artifact
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

    # Generate improvements for the mock artifact
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

def test_save_to_database():
    """Test saving generated content to the database."""
    print_section("TESTING DATABASE INTEGRATION")

    with app.app_context():
        # Create database tables if they don't exist
        db.create_all()

        # Initialize generators
        desc_generator = ProjectDescriptionGenerator()
        internal_generator = InternalMessagingGenerator()
        external_generator = ExternalMessagingGenerator()

        # Generate content
        project_content = json.dumps(TEST_PROJECT)
        description = desc_generator.generate(project_content)
        internal_msg = internal_generator.generate(project_content)
        external_msg = external_generator.generate(project_content)

        # Parse generated artifacts to extract objections and improvements
        description_data = json.loads(description)
        internal_data = json.loads(internal_msg)
        external_data = json.loads(external_msg)

        # Extract objections
        description_objections = json.dumps(description_data.get('objections', []))
        internal_objections = json.dumps(internal_data.get('objections', []))
        external_objections = json.dumps(external_data.get('objections', []))

        # Extract improvements
        description_improvements = json.dumps(description_data.get('improvements', []))
        internal_improvements = json.dumps(internal_data.get('improvements', []))
        external_improvements = json.dumps(external_data.get('improvements', []))

        # Create a new project record
        project = Project(
            content=project_content,
            description=description,
            internal_messaging=internal_msg,
            external_messaging=external_msg,
            description_objections=description_objections,
            internal_objections=internal_objections,
            external_objections=external_objections,
            description_improvements=description_improvements,
            internal_improvements=internal_improvements,
            external_improvements=external_improvements,
            timestamp=datetime.utcnow()
        )

        # Save to database
        db.session.add(project)
        db.session.commit()

        # Verify saved
        saved_project = Project.query.order_by(Project.timestamp.desc()).first()
        print(f"Project saved to database with ID: {saved_project.id}")
        print(f"Timestamp: {saved_project.timestamp}")
        print("Content includes:")
        print(f"- Description: {'Yes' if saved_project.description else 'No'}")
        print(f"- Internal Messaging: {'Yes' if saved_project.internal_messaging else 'No'}")
        print(f"- External Messaging: {'Yes' if saved_project.external_messaging else 'No'}")
        print(f"- Description Objections: {'Yes' if saved_project.description_objections else 'No'}")
        print(f"- Internal Objections: {'Yes' if saved_project.internal_objections else 'No'}")
        print(f"- External Objections: {'Yes' if saved_project.external_objections else 'No'}")
        print(f"- Description Improvements: {'Yes' if saved_project.description_improvements else 'No'}")
        print(f"- Internal Improvements: {'Yes' if saved_project.internal_improvements else 'No'}")
        print(f"- External Improvements: {'Yes' if saved_project.external_improvements else 'No'}")

if __name__ == "__main__":
    print("Project Alignment Tool Test Script")
    print("=================================")
    print("This script demonstrates the functionality of the Project Alignment Tool")
    print("including content generation, objections, and improvements.")
    print("\nYou need to have a valid Claude API key to run this test.")

    # Execute tests
    try:
        test_project_description()
        test_internal_messaging()
        test_external_messaging()
        test_direct_objection_generation()
        test_direct_improvement_generation()

        # Only run database test if specified
        if len(sys.argv) > 1 and sys.argv[1] == '--with-db':
            test_save_to_database()
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\nAll tests completed!")