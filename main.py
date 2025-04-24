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
from integrations.linear import LinearIntegration

# Import services
from services.sync_service import SyncService
from services.alignment_service import AlignmentService
from services.change_impact_analyzer import ChangeImpactAnalyzer

# Import artifact generators
from services.artifacts.project_description import ProjectDescriptionGenerator
from services.artifacts.internal_messaging import InternalMessagingGenerator
from services.artifacts.external_messaging import ExternalMessagingGenerator
from services.artifacts.objection_generator import ObjectionGenerator

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

# Connect integrations to sync service
sync_service.set_integrations(google_docs, jira, linear, confluence)

# Initialize artifact generators
project_description_generator = ProjectDescriptionGenerator()
internal_messaging_generator = InternalMessagingGenerator()
external_messaging_generator = ExternalMessagingGenerator()
objection_generator = ObjectionGenerator()

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

        # Analyze the connected document and generate initial artifacts
        project_content = sync_service.collect_all_content()

        # Generate artifacts
        description = project_description_generator.generate(project_content)
        internal_msg = internal_messaging_generator.generate(project_content)
        external_msg = external_messaging_generator.generate(project_content)

        # Parse generated artifacts to extract objections
        description_data = json.loads(description)
        internal_data = json.loads(internal_msg)
        external_data = json.loads(external_msg)

        # Extract objections
        description_objections = json.dumps(description_data.get('objections', []))
        internal_objections = json.dumps(internal_data.get('objections', []))
        external_objections = json.dumps(external_data.get('objections', []))

        # Save to project
        project = Project(
            content=project_content,
            description=description,
            internal_messaging=internal_msg,
            external_messaging=external_msg,
            description_objections=description_objections,
            internal_objections=internal_objections,
            external_objections=external_objections,
            timestamp=datetime.utcnow()
        )
        db.session.add(project)
        db.session.commit()

        flash('Document connected successfully!', 'success')
        return redirect(url_for('index'))