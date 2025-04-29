# integrations/google_docs.py
# This file contains the GoogleDocsIntegration class for connecting to Google Docs

import logging
import json
import random
from datetime import datetime
from flask import url_for, redirect, session
from integrations.content_extractor import ContentExtractor

class GoogleDocsIntegration:
    def __init__(self):
        """Initialize the Google Docs integration"""
        self.logger = logging.getLogger(__name__)
        self.connected_docs = []
        self.content_extractor = ContentExtractor()

        # Sample document content for demo/testing
        self.doc_content = {
            'prd': {
                'raw': """# Project Alignment Tool

## Overview
The Project Alignment Tool is a comprehensive system that ensures all project documentation remains synchronized across different platforms. By maintaining consistency between PRDs, PRFAQs, strategy documents, and tickets, it significantly reduces miscommunication and implementation errors.

## Problem Statement
Teams waste 4+ hours weekly reconciling inconsistent documentation across different systems. This leads to implementation errors, miscommunication, and project delays that frustrate both teams and customers.

## Solution
Our tool creates bidirectional connections between documents. When changes occur in any document, the system flags needed updates in all related documents, ensuring perfect alignment.""",
                'name': 'Project Alignment Tool',
                'overview': 'The Project Alignment Tool is a comprehensive system that ensures all project documentation remains synchronized across different platforms. By maintaining consistency between PRDs, PRFAQs, strategy documents, and tickets, it significantly reduces miscommunication and implementation errors.',
                'problem_statement': 'Teams waste 4+ hours weekly reconciling inconsistent documentation across different systems. This leads to implementation errors, miscommunication, and project delays that frustrate both teams and customers.',
                'solution': 'Our tool creates bidirectional connections between documents. When changes occur in any document, the system flags needed updates in all related documents, ensuring perfect alignment.'
            },
            'prfaq': {
                'raw': """# Document Sync Tool - Press Release

FOR IMMEDIATE RELEASE
Introducing the Document Sync Tool - a new solution that keeps your documentation in sync automatically.

## Frequently Asked Questions

Q: What problem does this solve?
A: Teams often have multiple documents (PRD, tickets, strategy) that get out of sync, causing confusion and implementation errors.

Q: How does it work?
A: The tool connects to all your project documents and detects changes, then suggests updates to keep everything aligned.

Q: What systems does it support?
A: We currently support Google Docs, Jira, Linear, and Confluence.""",
                'press_release': 'Introducing the Document Sync Tool - a new solution that keeps your documentation in sync automatically.',
                'frequently_asked_questions': [
                    {
                        'question': 'What problem does this solve?',
                        'answer': 'Teams often have multiple documents (PRD, tickets, strategy) that get out of sync, causing confusion and implementation errors.'
                    },
                    {
                        'question': 'How does it work?',
                        'answer': 'The tool connects to all your project documents and detects changes, then suggests updates to keep everything aligned.'
                    },
                    {
                        'question': 'What systems does it support?',
                        'answer': 'We currently support Google Docs, Jira, Linear, and Confluence.'
                    }
                ]
            },
            'strategy': {
                'raw': """# Project Alignment Strategy

## Vision
Create the best tool for maintaining project alignment through synchronized documentation.

## Approach
Focus on simplicity and actionable suggestions, using AI and bidirectional links.

## Business Value
Reduce errors due to misalignment by 40% and save team time spent reconciling documents.""",
                'vision': 'Create the best tool for maintaining project alignment through synchronized documentation.',
                'approach': 'Focus on simplicity and actionable suggestions, using AI and bidirectional links.',
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
        """
        Connect a Google Doc

        Args:
            doc_id (str): Document ID

        Returns:
            bool: True if connection was successful
        """
        # Determine document type based on ID
        doc_type = 'prd'
        if 'prfaq' in doc_id.lower():
            doc_type = 'prfaq'
        elif 'strategy' in doc_id.lower():
            doc_type = 'strategy'

        # Add to connected docs
        self.connected_docs.append({
            'id': doc_id,
            'type': doc_type,
            'connected_at': datetime.utcnow()
        })
        self.logger.info(f"Connected document {doc_id} of type {doc_type}")
        return True

    def get_connected_docs(self):
        """
        Get list of connected documents

        Returns:
            list: Connected documents
        """
        return self.connected_docs

    def get_document_type(self, doc_id):
        """
        Get document type from ID

        Args:
            doc_id (str): Document ID

        Returns:
            str: Document type or None if not found
        """
        for doc in self.connected_docs:
            if doc['id'] == doc_id:
                return doc['type']
        return None

    def get_document_content(self, doc_id):
        """
        Get document content with structured extraction

        Args:
            doc_id (str): Document ID

        Returns:
            dict: Structured document content
        """
        # Get document type
        doc_type = self.get_document_type(doc_id)
        if not doc_type:
            self.logger.error(f"Unknown document type for {doc_id}")
            return {}

        # Get raw content
        raw_content = self._fetch_raw_content(doc_id)

        # Extract structured content using ContentExtractor
        structured_content = self.content_extractor.extract_structure(raw_content, doc_type)

        self.logger.info(f"Extracted structured content from {doc_id} with {len(structured_content)} sections")
        return structured_content

    def _fetch_raw_content(self, doc_id):
        """
        Mock fetching raw content from Google Docs

        Args:
            doc_id (str): Document ID

        Returns:
            str: Raw document content
        """
        # In a real implementation, this would use the Google Docs API
        # For the mock implementation, return sample content
        doc_type = self.get_document_type(doc_id)

        if doc_type and doc_type in self.doc_content:
            return self.doc_content[doc_type]['raw']

        return "# Untitled Document\n\nNo content available"