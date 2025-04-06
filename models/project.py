# models/project.py
from . import db
from datetime import datetime
import json

class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)  # JSON string of all project content
    description = db.Column(db.Text, nullable=True)  # Generated project description
    internal_messaging = db.Column(db.Text, nullable=True)  # Generated internal messaging
    external_messaging = db.Column(db.Text, nullable=True)  # Generated external messaging
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def get_content_dict(self):
        """Return content as a dictionary"""
        return json.loads(self.content)

    def __repr__(self):
        return f'<Project {self.id} {self.timestamp}>'