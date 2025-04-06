import os
import json
import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime

from config import Config
from models import db, Version, Project, Alignment
from integrations.google_docs import GoogleDocsIntegration
from integrations.jira import JiraIntegration
from integrations.confluence import ConfluenceIntegration

# Import services
from services.sync_service import SyncService
from services.alignment_service import AlignmentService
from services.change_impact_analyzer import ChangeImpactAnalyzer

# Import artifact generators
from services.artifacts.project_description import ProjectDescriptionGenerator
from services.artifacts.internal_messaging import InternalMessagingGenerator
from services.artifacts.external_messaging import ExternalMessagingGenerator

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
confluence = ConfluenceIntegration()

# Initialize services
sync_service = SyncService()
alignment_service = AlignmentService()
impact_analyzer = ChangeImpactAnalyzer()

# Connect integrations to sync service
sync_service.set_integrations(google_docs, jira, None, confluence)

# Initialize artifact generators
project_description_generator = ProjectDescriptionGenerator()
internal_messaging_generator = InternalMessagingGenerator()
external_messaging_generator = ExternalMessagingGenerator()

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
        elif doc_type == 'confluence':
            confluence.connect_page(doc_id)

        # Analyze the connected document and generate initial artifacts
        project_content = sync_service.collect_all_content()

        # Generate artifacts
        description = project_description_generator.generate(project_content)
        internal_msg = internal_messaging_generator.generate(project_content)
        external_msg = external_messaging_generator.generate(project_content)

        # Save to project
        project = Project(
            content=project_content,
            description=description,
            internal_messaging=internal_msg,
            external_messaging=external_msg,
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
        # Collect all content
        project_content = sync_service.collect_all_content()

        # Analyze changes
        changes = alignment_service.analyze_changes(project_content)
        impact = impact_analyzer.analyze(changes)

        # Generate updated artifacts
        description = project_description_generator.generate(project_content)
        internal_msg = internal_messaging_generator.generate(project_content, changes)
        external_msg = external_messaging_generator.generate(project_content, changes)

        # Save to project
        project = Project(
            content=project_content,
            description=description,
            internal_messaging=internal_msg,
            external_messaging=external_msg,
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

            # Save to project
            project = Project(
                content=project_content,
                description=description,
                internal_messaging=internal_msg,
                external_messaging=external_msg,
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
        project_content = {
            'prd': {},
            'prfaq': {},
            'strategy': {},
            'tickets': []
        }

        # Add content to the appropriate section
        if mock_type == 'prd':
            project_content['prd'] = {
                'overview': content,
                'problem_statement': 'Extracted problem statement',
                'solution': 'Extracted solution approach'
            }
        elif mock_type == 'prfaq':
            project_content['prfaq'] = {
                'press_release': content,
                'frequently_asked_questions': [
                    {'question': 'What problem does this solve?', 'answer': 'Extracted problem statement'}
                ]
            }
        elif mock_type == 'strategy':
            project_content['strategy'] = {
                'vision': content,
                'approach': 'Extracted strategic approach'
            }

        # Generate artifacts
        project_content_json = json.dumps(project_content)
        description = project_description_generator.generate(project_content_json)
        internal_msg = internal_messaging_generator.generate(project_content_json)
        external_msg = external_messaging_generator.generate(project_content_json)

        # Return results
        return render_template('test_results.html',
                              content=content,
                              description=json.loads(description),
                              internal=json.loads(internal_msg),
                              external=json.loads(external_msg))

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
            'suggestions': alignment.suggestions,
            'impact': alignment.impact_analysis,
            'timestamp': alignment.timestamp
        })
    return jsonify({'suggestions': [], 'impact': None, 'timestamp': None})

@app.route('/api/artifacts', methods=['GET'])
def api_artifacts():
    """API endpoint to get latest artifacts"""
    project = Project.query.order_by(Project.timestamp.desc()).first()
    if project:
        return jsonify({
            'description': project.description,
            'internal_messaging': project.internal_messaging,
            'external_messaging': project.external_messaging,
            'timestamp': project.timestamp
        })
    return jsonify({
        'description': None,
        'internal_messaging': None,
        'external_messaging': None,
        'timestamp': None
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)