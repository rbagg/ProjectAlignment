# models/project.py
from . import db
from datetime import datetime
import json

class Project(db.Model):
    """
    Project model for storing project content and generated artifacts.

    This model represents a snapshot of a project at a specific point in time,
    including its content and generated artifacts like descriptions and messaging.
    """
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)  # JSON string of all project content
    description = db.Column(db.Text, nullable=True)  # Generated project description
    internal_messaging = db.Column(db.Text, nullable=True)  # Generated internal messaging
    external_messaging = db.Column(db.Text, nullable=True)  # Generated external messaging
    description_objections = db.Column(db.Text, nullable=True)  # Objections to project description
    internal_objections = db.Column(db.Text, nullable=True)  # Objections to internal messaging
    external_objections = db.Column(db.Text, nullable=True)  # Objections to external messaging
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def get_content_dict(self):
        """Return content as a dictionary"""
        try:
            return json.loads(self.content)
        except json.JSONDecodeError:
            # Return empty dict if content is invalid JSON
            return {}

    def get_description_dict(self):
        """Return description as a dictionary"""
        try:
            return json.loads(self.description) if self.description else {}
        except json.JSONDecodeError:
            return {}

    def get_internal_messaging_dict(self):
        """Return internal messaging as a dictionary"""
        try:
            return json.loads(self.internal_messaging) if self.internal_messaging else {}
        except json.JSONDecodeError:
            return {}

    def get_external_messaging_dict(self):
        """Return external messaging as a dictionary"""
        try:
            return json.loads(self.external_messaging) if self.external_messaging else {}
        except json.JSONDecodeError:
            return {}

    def get_description_objections_list(self):
        """Return description objections as a list"""
        try:
            return json.loads(self.description_objections) if self.description_objections else []
        except json.JSONDecodeError:
            return []

    def get_internal_objections_list(self):
        """Return internal messaging objections as a list"""
        try:
            return json.loads(self.internal_objections) if self.internal_objections else []
        except json.JSONDecodeError:
            return []

    def get_external_objections_list(self):
        """Return external messaging objections as a list"""
        try:
            return json.loads(self.external_objections) if self.external_objections else []
        except json.JSONDecodeError:
            return []

    def __repr__(self):
        return f'<Project {self.id} {self.timestamp}>'