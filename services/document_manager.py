# services/document_manager.py
# This file contains the DocumentManager class for managing document processing

import logging
import json
from integrations.content_extractor import ContentExtractor
from services.document_validator import DocumentValidator

class DocumentManager:
    """Centralized manager for document processing and integration"""

    def __init__(self):
        """Initialize the DocumentManager with necessary components"""
        self.logger = logging.getLogger(__name__)
        self.content_extractor = ContentExtractor()
        self.document_validator = DocumentValidator()
        self.integrations = {}  # Will hold integration instances

    def register_integration(self, name, integration):
        """
        Register an integration instance

        Args:
            name (str): Integration name
            integration (object): Integration instance
        """
        self.integrations[name] = integration
        self.logger.info(f"Registered integration: {name}")

    def process_document(self, doc_id, doc_type, integration_type):
        """
        Process a document from a specific integration

        Args:
            doc_id (str): Document ID
            doc_type (str): Document type (prd, prfaq, strategy)
            integration_type (str): Integration type (google_docs, confluence, etc.)

        Returns:
            dict: Processed document with content, metadata, and analysis
        """
        # Verify integration is registered
        if integration_type not in self.integrations:
            self.logger.error(f"Unknown integration type: {integration_type}")
            return None

        integration = self.integrations[integration_type]

        # Process and extract document content
        try:
            # Get raw content from the integration
            raw_content = integration.get_document_content(doc_id)

            # Extract structured content if not already structured
            if isinstance(raw_content, str):
                structured_content = self.content_extractor.extract_structure(raw_content, doc_type)
            else:
                structured_content = raw_content

            # Validate document structure
            validation = self.document_validator.validate_document(structured_content, doc_type)

            # Extract metadata
            metadata = self._extract_metadata(structured_content, doc_type)

            # Generate improvement suggestions if validation failed
            if not validation['valid']:
                improvement_suggestions = self.document_validator.suggest_improvements(
                    validation, structured_content, doc_type)
            else:
                improvement_suggestions = []

            # Return combined results
            return {
                'document_id': doc_id,
                'document_type': doc_type,
                'integration_type': integration_type,
                'content': structured_content,
                'metadata': metadata,
                'validation': validation,
                'suggestions': improvement_suggestions
            }

        except Exception as e:
            self.logger.error(f"Error processing document {doc_id}: {str(e)}")
            return None

    def _extract_metadata(self, structured_content, doc_type):
        """
        Extract metadata from document content

        Args:
            structured_content (dict): Structured document content
            doc_type (str): Document type

        Returns:
            dict: Document metadata
        """
        metadata = {
            'title': self._get_document_title(structured_content, doc_type),
            'length': self._calculate_document_length(structured_content)
        }

        return metadata

    def _get_document_title(self, structured_content, doc_type):
        """
        Extract document title based on document type

        Args:
            structured_content (dict): Structured document content
            doc_type (str): Document type

        Returns:
            str: Document title
        """
        if 'name' in structured_content:
            return structured_content['name']

        if doc_type == 'prd' and 'overview' in structured_content:
            # Try to extract title from first line of overview
            overview = structured_content['overview']
            first_line = overview.split('\n')[0].strip()
            if first_line and len(first_line) < 100:
                return first_line

        if doc_type == 'prfaq' and 'press_release' in structured_content:
            # Try to extract title from press release
            press_release = structured_content['press_release']
            first_line = press_release.split('\n')[0].strip()
            if first_line and len(first_line) < 100:
                return first_line

        # Default title if nothing found
        return f"Untitled {doc_type.upper()}"

    def _calculate_document_length(self, structured_content):
        """
        Calculate the length of document content

        Args:
            structured_content (dict): Structured document content

        Returns:
            dict: Document length metrics
        """
        total_chars = 0
        total_words = 0
        total_sections = 0

        for section_name, section_content in structured_content.items():
            if isinstance(section_content, str):
                # Count characters and words in string content
                total_chars += len(section_content)
                total_words += len(section_content.split())
                total_sections += 1
            elif isinstance(section_content, list):
                # Count characters and words in list content
                for item in section_content:
                    if isinstance(item, str):
                        total_chars += len(item)
                        total_words += len(item.split())
                    elif isinstance(item, dict):
                        for value in item.values():
                            if isinstance(value, str):
                                total_chars += len(value)
                                total_words += len(value.split())
                total_sections += 1

        return {
            'characters': total_chars,
            'words': total_words,
            'sections': total_sections
        }