# models/alignment.py
from . import db
from datetime import datetime
import json

class Alignment(db.Model):
    __tablename__ = 'alignments'

    id = db.Column(db.Integer, primary_key=True)
    suggestions = db.Column(db.Text, nullable=False)  # JSON string of alignment suggestions
    impact_analysis = db.Column(db.Text, nullable=True)  # JSON string of impact analysis
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def get_suggestions_list(self):
        """Return suggestions as a list"""
        return json.loads(self.suggestions)

    def get_impact_dict(self):
        """Return impact analysis as a dictionary"""
        return json.loads(self.impact_analysis) if self.impact_analysis else {}

    def __repr__(self):
        return f'<Alignment {self.id} {self.timestamp}>'