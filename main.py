# main.py
# This is the main application file with updated document extraction capabilities

import os
import json
import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime

from config import Config
from models import db, Version, Project, Alignment
from integrations.google_docs import GoogleDocsIntegration
from integrations.jira import JiraIntegration
from integrations.confluence import ConfluenceIntegration
from integrations.linear import LinearIntegration

# Import services
from services.sync_service import SyncService
from services.alignment_service import AlignmentService
from services.change_impact_analyzer import ChangeImpactAnalyzer
from services.document_manager import DocumentManager  # Import the new document manager
from integrations.content_extractor import ContentExtractor
from services.document_validator import DocumentValidator  # Import the new document validator

# Import artifact generators
from services.artifacts.project_description import ProjectDescriptionGenerator
from services.artifacts.internal_messaging import InternalMessagingGenerator
from services.artifacts.external_messaging import ExternalMessagingGenerator
from services.artifacts.objection_generator import ObjectionGenerator
from services.artifacts.improvement_generator import ImprovementGenerator

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per day", "10 per hour"]
)

# Initialize integrations
google_docs = GoogleDocsIntegration()
jira = JiraIntegration()
linear = LinearIntegration()
confluence = ConfluenceIntegration()

# Initialize services
sync_service = SyncService()
alignment_service = AlignmentService()
impact_analyzer = ChangeImpactAnalyzer()
document_manager = DocumentManager()  # Create document manager instance

# Connect integrations to sync service
sync_service.set_integrations(google_docs, jira, linear, confluence)

# Initialize artifact generators
project_description_generator = ProjectDescriptionGenerator()
internal_messaging_generator = InternalMessagingGenerator()
external_messaging_generator = ExternalMessagingGenerator()
objection_generator = ObjectionGenerator()
improvement_generator = ImprovementGenerator()

# Register integrations with document manager
document_manager.register_integration('google_docs', google_docs)
document_manager.register_integration('jira', jira)
document_manager.register_integration('linear', linear)
document_manager.register_integration('confluence', confluence)

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    if 'google_token' not in session:
        return redirect(url_for('setup'))

    # Get the current project
    project = Project.query.order_by(Project.timestamp.desc()).first()

    # Get latest alignment suggestions
    suggestions = alignment_service.get_suggestions()

    # Get latest artifacts
    artifacts = {
        'description': project_description_generator.get_latest() if project else None,
        'internal': internal_messaging_generator.get_latest() if project else None,
        'external': external_messaging_generator.get_latest() if project else None
    }

    return render_template('index.html', 
                         project=project,
                         suggestions=suggestions,
                         artifacts=artifacts)

@app.route('/setup')
def setup():
    return render_template('setup.html')

@app.route('/auth/google')
@limiter.limit("10 per hour")
def google_auth():
    return google_docs.authorize()

@app.route('/auth/callback')
def google_callback():
    token = google_docs.callback(request.args)
    session['google_token'] = token
    return redirect(url_for('index'))

@app.route('/connect', methods=['POST'])
@limiter.limit("10 per hour")
def connect_document():
    """Connect a document to the project (PRD, PRFAQ, tickets, etc.)"""
    try:
        doc_type = request.form.get('type')
        doc_id = request.form.get('id')

        # Connect the document
        if doc_type == 'google_docs':
            google_docs.connect_document(doc_id)
        elif doc_type == 'jira':
            jira.connect_project(doc_id)
        elif doc_type == 'linear':
            linear.connect_project(doc_id)
        elif doc_type == 'confluence':
            confluence.connect_page(doc_id)

        # Process document using the document manager for better extraction
        processed_doc = None
        if doc_type == 'google_docs':
            # Determine document type based on naming convention or user selection
            doc_subtype = 'prd'  # Default
            if 'prfaq' in doc_id.lower():
                doc_subtype = 'prfaq'
            elif 'strategy' in doc_id.lower():
                doc_subtype = 'strategy'

            # Process the document
            processed_doc = document_manager.process_document(
                doc_id=doc_id,
                doc_type=doc_subtype,
                integration_type=doc_type
            )

            # Log validation results
            if processed_doc and 'validation' in processed_doc:
                validation = processed_doc['validation']
                if not validation['valid']:
                    logger.info(f"Document validation issues: {validation}")
                    flash_msg = "Document connected, but has some issues: "
                    if validation.get('missing_sections'):
                        flash_msg += f"Missing sections: {', '.join(validation['missing_sections'])}. "
                    flash(flash_msg, 'warning')

        # Analyze the connected document and generate initial artifacts
        project_content = sync_service.collect_all_content()

        # Generate artifacts
        description = project_description_generator.generate(project_content)
        internal_msg = internal_messaging_generator.generate(project_content)
        external_msg = external_messaging_generator.generate(project_content)

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

        # Save to project
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
        db.session.add(project)
        db.session.commit()

        flash('Document connected successfully!', 'success')
        return redirect(url_for('index'))

    except Exception as e:
        logger.error(f"Error connecting document: {str(e)}")
        flash(f'Error connecting document: {str(e)}', 'error')
        return redirect(url_for('setup'))

@app.route('/update', methods=['POST'])
@limiter.limit("10 per hour")
def manual_update():
    """Manually trigger an update and alignment check"""
    try:
        # Collect all content with improved document extraction
        project_content = sync_service.collect_all_content()

        # Analyze changes
        changes = alignment_service.analyze_changes(project_content)
        impact = impact_analyzer.analyze(changes)

        # Generate updated artifacts
        description = project_description_generator.generate(project_content)
        internal_msg = internal_messaging_generator.generate(project_content, changes)
        external_msg = external_messaging_generator.generate(project_content, changes)

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

        # Save to project
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
        db.session.add(project)

        # Save alignment suggestions
        alignment = Alignment(
            suggestions=alignment_service.format_suggestions(changes),
            impact_analysis=impact,
            timestamp=datetime.utcnow()
        )
        db.session.add(alignment)
        db.session.commit()

        flash('Project updated and aligned successfully!', 'success')
        return redirect(url_for('index'))

    except Exception as e:
        logger.error(f"Error updating project: {str(e)}")
        flash(f'Error updating project: {str(e)}', 'error')
        return redirect(url_for('index'))

# New route to inspect document structure
@app.route('/document/inspect', methods=['GET', 'POST'])
def inspect_document():
    """
    Inspect document structure using the improved extraction capabilities.
    This allows users to see how the system extracts structured content from documents.
    """
    if request.method == 'POST':
        # Process file upload or text input
        content = ""
        doc_type = request.form.get('doc_type', 'prd')

        if 'file' in request.files and request.files['file'].filename:
            file = request.files['file']
            content = file.read().decode('utf-8')
        elif request.form.get('content'):
            content = request.form.get('content')
        else:
            flash('Please provide either a file or text content', 'error')
            return redirect(url_for('inspect_document'))

        try:
            # Extract structured content with improved generic extractor
            content_extractor = ContentExtractor()

            # First try a generic extraction
            structured_content = content_extractor.extract_structure(content)

            # Then use the document type hint for enhanced extraction
            structured_content = content_extractor.extract_structure(content, doc_type)

            # Validate structure with improved flexible validator
            document_validator = DocumentValidator()
            validation = document_validator.validate_document(structured_content, doc_type)

            # Generate improvement suggestions if needed
            suggestions = document_validator.suggest_improvements(validation, structured_content, doc_type)

            # Calculate metadata
            metadata = {
                'title': structured_content.get('name', doc_type.upper()),
                'length': document_manager._calculate_document_length(structured_content),
                'detected_type': validation.get('identified_type', doc_type)
            }

            # Render the results
            return render_template(
                'document_inspector_results.html',
                raw_content=content,
                structured_content=structured_content,
                validation=validation,
                suggestions=suggestions,
                metadata=metadata,
                doc_type=doc_type
            )

        except Exception as e:
            logger.error(f"Error inspecting document: {str(e)}")
            flash(f'Error inspecting document: {str(e)}', 'error')
            return redirect(url_for('inspect_document'))

    # Show the upload form
    return render_template('document_inspector.html')

@app.route('/webhook', methods=['POST'])
@limiter.limit("100 per hour")
def webhook():
    """Handle updates from connected platforms"""
    try:
        data = request.json
        source = data.get('source')

        # Process the update based on source
        if source == 'jira':
            changes = sync_service.handle_jira_update(data)
        elif source == 'google_docs':
            changes = sync_service.handle_docs_update(data)
        elif source == 'confluence':
            changes = sync_service.handle_confluence_update(data)
        elif source == 'linear':
            changes = sync_service.handle_linear_update(data)
        else:
            return {'error': 'Unknown source'}, 400

        # If changes were detected, analyze and generate artifacts
        if changes:
            # Get the latest project content
            project_content = sync_service.collect_all_content()

            # Analyze impact
            impact = impact_analyzer.analyze(changes)

            # Generate updated artifacts
            description = project_description_generator.generate(project_content)
            internal_msg = internal_messaging_generator.generate(project_content, changes)
            external_msg = external_messaging_generator.generate(project_content, changes)

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

            # Save to project
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
            db.session.add(project)

            # Save alignment suggestions
            alignment = Alignment(
                suggestions=alignment_service.format_suggestions(changes),
                impact_analysis=impact,
                timestamp=datetime.utcnow()
            )
            db.session.add(alignment)
            db.session.commit()

        return {'status': 'success', 'changes_detected': bool(changes)}, 200

    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return {'error': str(e)}, 500

# Test routes for artifact generation
@app.route('/test', methods=['GET'])
def test_form():
    """Display test form for artifact generation"""
    return render_template('test.html')

@app.route('/test/generate', methods=['POST'])
def test_generation():
    """Test artifact generation with provided content"""
    try:
        # Get uploaded file or text input
        content = ""
        if 'file' in request.files and request.files['file'].filename:
            file = request.files['file']
            content = file.read().decode('utf-8')
        elif request.form.get('content'):
            content = request.form.get('content')
        else:
            flash('Please provide either a file or text content', 'error')
            return redirect(url_for('test_form'))

        # Create a mock project structure
        mock_type = request.form.get('mock_type', 'prd')

        # Use the content extractor for better structure extraction
        content_extractor = ContentExtractor()
        structured_content = content_extractor.extract_structure(content, mock_type)

        # Create the project content structure
        project_content = {
            'prd': {},
            'prfaq': {},
            'strategy': {},
            'tickets': []
        }

        # Add content to the appropriate section
        if mock_type == 'prd':
            project_content['prd'] = structured_content
        elif mock_type == 'prfaq':
            project_content['prfaq'] = structured_content
        elif mock_type == 'strategy':
            project_content['strategy'] = structured_content

        # Generate artifacts
        project_content_json = json.dumps(project_content)
        description = project_description_generator.generate(project_content_json)
        internal_msg = internal_messaging_generator.generate(project_content_json)
        external_msg = external_messaging_generator.generate(project_content_json)

        # Parse the results
        description_data = json.loads(description)
        internal_data = json.loads(internal_msg)
        external_data = json.loads(external_msg)

        # Return results
        return render_template('test_results.html',
                              content=content,
                              description=description_data,
                              internal=internal_data,
                              external=external_data)

    except Exception as e:
        logger.error(f"Test generation error: {str(e)}")
        flash(f'Error generating artifacts: {str(e)}', 'error')
        return redirect(url_for('test_form'))

@app.route('/api/suggestions', methods=['GET'])
def api_suggestions():
    """API endpoint to get latest suggestions"""
    alignment = Alignment.query.order_by(Alignment.timestamp.desc()).first()
    if alignment:
        return jsonify({
            'suggestions': json.loads(alignment.suggestions) if alignment.suggestions else [],
            'impact': json.loads(alignment.impact_analysis) if alignment.impact_analysis else None,
            'timestamp': alignment.timestamp
        })
    return jsonify({'suggestions': [], 'impact': None, 'timestamp': None})

@app.route('/api/artifacts', methods=['GET'])
def api_artifacts():
    """API endpoint to get latest artifacts"""
    project = Project.query.order_by(Project.timestamp.desc()).first()
    if project:
        description = project.get_description_dict()
        internal = project.get_internal_messaging_dict()
        external = project.get_external_messaging_dict()

        # Add objections
        if project.description_objections:
            description['objections'] = project.get_description_objections_list()
        if project.internal_objections:
            internal['objections'] = project.get_internal_objections_list()
        if project.external_objections:
            external['objections'] = project.get_external_objections_list()

        # Add improvements
        if project.description_improvements:
            description['improvements'] = project.get_description_improvements_list()
        if project.internal_improvements:
            internal['improvements'] = project.get_internal_improvements_list()
        if project.external_improvements:
            external['improvements'] = project.get_external_improvements_list()

        return jsonify({
            'description': description,
            'internal_messaging': internal,
            'external_messaging': external,
            'timestamp': project.timestamp
        })
    return jsonify({
        'description': None,
        'internal_messaging': None,
        'external_messaging': None,
        'timestamp': None
    })

@app.route('/api/objections', methods=['GET'])
def api_objections():
    """API endpoint to get latest objections"""
    project = Project.query.order_by(Project.timestamp.desc()).first()
    if project:
        return jsonify({
            'description_objections': project.get_description_objections_list(),
            'internal_objections': project.get_internal_objections_list(),
            'external_objections': project.get_external_objections_list(),
            'timestamp': project.timestamp
        })
    return jsonify({
        'description_objections': [],
        'internal_objections': [],
        'external_objections': [],
        'timestamp': None
    })

@app.route('/api/improvements', methods=['GET'])
def api_improvements():
    """API endpoint to get latest improvements"""
    project = Project.query.order_by(Project.timestamp.desc()).first()
    if project:
        return jsonify({
            'description_improvements': project.get_description_improvements_list(),
            'internal_improvements': project.get_internal_improvements_list(),
            'external_improvements': project.get_external_improvements_list(),
            'timestamp': project.timestamp
        })
    return jsonify({
        'description_improvements': [],
        'internal_improvements': [],
        'external_improvements': [],
        'timestamp': None
    })

@app.route('/examples')
def test_examples():
    """Display examples of all generators"""
    # Try to get cached examples from session
    example_data = session.get('example_data')

    # If no examples in session, generate them
    if not example_data:
        example_data = generate_examples()
        session['example_data'] = example_data

    return render_template('test_examples.html', example_data=example_data)

@app.route('/examples/refresh')
def refresh_examples():
    """Regenerate examples"""
    # Clear any cached examples
    if 'example_data' in session:
        session.pop('example_data')

    # Generate fresh examples
    example_data = generate_examples()
    session['example_data'] = example_data

    flash('Examples refreshed successfully!', 'success')
    return redirect(url_for('test_examples'))

def generate_examples():
    """Generate examples using all generators"""
    # Use the test project data
    test_project = {
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
                    'answer': 'Teams waste hours weekly reconciling inconsistent documentation.'
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
            'business_value': 'Save teams hours per week and reduce implementation errors.'
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

    # Convert to JSON string as required by generators
    project_content_json = json.dumps(test_project)

    try:
        logger.info("Generating real examples using generators...")

        # Generate project description using real generator
        logger.info("Generating project description...")
        description_json = project_description_generator.generate(project_content_json)
        description_data = json.loads(description_json)

        # Generate internal messaging using real generator
        logger.info("Generating internal messaging...")
        internal_json = internal_messaging_generator.generate(project_content_json)
        internal_data = json.loads(internal_json)

        # Generate external messaging using real generator
        logger.info("Generating external messaging...")
        external_json = external_messaging_generator.generate(project_content_json)
        external_data = json.loads(external_json)

        # Create input artifact for direct objection/improvement tests
        objection_input = {
            'headline': 'Save hours per week on documentation',
            'description': 'Our tool automatically syncs your documents and keeps everything aligned.'
        }

        # Generate direct objections using real generator
        logger.info("Generating direct objections...")
        direct_objections_json = objection_generator.generate_for_artifact(
            test_project, objection_input, 'external')
        direct_objections = json.loads(direct_objections_json)

        # Log the format of the first objection to verify new fields
        if direct_objections and len(direct_objections) > 0:
            logger.info(f"Sample direct objection format: {json.dumps(direct_objections[0], indent=2)}")

        # Generate direct improvements using real generator
        logger.info("Generating direct improvements...")
        direct_improvements_json = improvement_generator.generate_for_artifact(
            test_project, objection_input, 'external')
        direct_improvements = json.loads(direct_improvements_json)

        # Log the format of the first improvement to verify new fields
        if direct_improvements and len(direct_improvements) > 0:
            logger.info(f"Sample direct improvement format: {json.dumps(direct_improvements[0], indent=2)}")

        # Combine all data into example_data dictionary
        example_data = {
            'description': description_data,
            'internal': internal_data,
            'external': external_data,
            'direct_objections': direct_objections,
            'direct_improvements': direct_improvements,
            'objection_input': objection_input,
            'improvement_input': objection_input  # Same input used for both
        }

        logger.info("Successfully generated all examples with real generators")

    except Exception as e:
        logger.error(f"Error generating examples with real generators: {str(e)}")
    
    return example_data

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)