# integrations/google_docs.py
import logging
import json
import random
from datetime import datetime
from flask import url_for, redirect, session

logger = logging.getLogger(__name__)

class GoogleDocsIntegration:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connected_docs = []
        self.doc_content = {
            'prd': {
                'name': 'Project Alignment Tool',
                'overview': 'Keep all project documents in sync and maintain alignment across PRD, tickets, and strategy.',
                'problem_statement': 'Teams struggle with keeping documentation in sync, leading to misalignment between PRD and implementation.',
                'solution': 'Create a tool that monitors changes to all project documents and suggests updates to maintain alignment.'
            },
            'prfaq': {
                'press_release': 'Introducing the Project Alignment Tool - a new solution that keeps your documentation in sync automatically.',
                'frequently_asked_questions': [
                    {
                        'question': 'What problem does this solve?',
                        'answer': 'Teams often have multiple documents (PRD, tickets, strategy) that get out of sync, causing confusion and implementation errors.'
                    },
                    {
                        'question': 'How does it work?',
                        'answer': 'The tool connects to all your project documents and detects changes, then suggests updates to keep everything aligned.'
                    }
                ]
            },
            'strategy': {
                'vision': 'Create the best tool for maintaining project alignment.',
                'approach': 'Focus on simplicity and actionable suggestions.',
                'business_value': 'Reduce errors due to misalignment by 40% and save team time spent reconciling documents.'
            }
        }

    def authorize(self):
        """Mock Google authorization"""
        return redirect(url_for('google_callback'))

    def callback(self, args):
        """Mock Google callback"""
        return 'mock-google-token'

    def connect_document(self, doc_id):
        """Mock connecting a document"""
        doc_type = 'prd'
        if 'prfaq' in doc_id.lower():
            doc_type = 'prfaq'
        elif 'strategy' in doc_id.lower():
            doc_type = 'strategy'

        self.connected_docs.append({
            'id': doc_id,
            'type': doc_type,
            'connected_at': datetime.utcnow()
        })
        return True

    def get_connected_docs(self):
        """Get list of connected documents"""
        return self.connected_docs

    def get_document_type(self, doc_id):
        """Get document type from ID"""
        for doc in self.connected_docs:
            if doc['id'] == doc_id:
                return doc['type']
        return None

    def get_document_content(self, doc_id):
        """Mock getting document content"""
        doc_type = self.get_document_type(doc_id)
        if doc_type:
            return self.doc_content.get(doc_type, {})
        return {}