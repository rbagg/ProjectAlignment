# Updated Project Alignment Tool Architecture

This document outlines the improved architecture for the Project Alignment Tool, with enhancements to implement the critical objection-generation feature and improve overall code quality.

## Project Structure

```
project-alignment-tool/
│
├── integrations/                      # External service integrations
│   ├── __init__.py                    # Package initialization
│   ├── confluence.py                  # Confluence API integration
│   ├── google_docs.py                 # Google Docs API integration
│   ├── jira.py                        # Jira API integration
│   └── linear.py                      # Linear API integration
│
├── models/                            # Database models
│   ├── __init__.py                    # Database initialization
│   ├── alignment.py                   # Alignment model for suggestions
│   ├── project.py                     # Project model for content storage
│   └── version.py                     # Version history model
│
├── services/                          # Core business logic
│   ├── artifacts/                     # Content generation services
│   │   ├── __init__.py                # Package initialization
│   │   ├── base_generator.py          # Base class for generators
│   │   ├── external_messaging.py      # Customer-facing message generator
│   │   ├── internal_messaging.py      # Team communication generator
│   │   ├── objection_generator.py     # Objection generation service
│   │   └── project_description.py     # Project summary generator
│   │
│   ├── __init__.py                    # Package initialization
│   ├── alignment_service.py           # Alignment analysis service
│   ├── change_impact_analyzer.py      # Change impact evaluation
│   └── sync_service.py                # Document synchronization
│
├── static/                            # Static assets
│   └── css/
│       └── minimal.css                # Minimal CSS styling
│
├── templates/                         # HTML templates
│   ├── base.html                      # Base template layout
│   ├── dashboard.html                 # Dashboard view
│   ├── index.html                     # Main dashboard (updated with objections)
│   ├── setup.html                     # Integration setup
│   ├── test.html                      # Testing interface
│   └── test_results.html              # Test generation results (with objections)
│
├── .gitignore                         # Git ignore rules
├── .replit                            # Replit configuration
├── ARCHITECTURE.md                    # This architecture document
├── README.md                          # Project documentation
├── config.py                          # Application configuration
├── main.py                            # Application entry point (updated)
├── pyproject.toml                     # Python project metadata
├── requirements.txt                   # Python dependencies
└── uv.lock                            # Dependency lock file
```

## Key Enhancements

1. **Added Objection Generation**:
   - New service for generating critical objections to messaging
   - Integration with all artifact generators
   - Updated UI to display objections

2. **Improved AI Prompts**:
   - All prompts now follow the master prompt structure
   - Consistent formatting and approach across generators
   - Better quality assurance and error handling

3. **Enhanced Code Structure**:
   - Added base generator class for common functionality
   - Fixed broken code in internal messaging generator
   - Improved error handling and recovery mechanisms

4. **Updated Data Models**:
   - Project model now includes objections field
   - Better JSON serialization and deserialization

5. **Improved User Interface**:
   - New section for displaying objections
   - Enhanced error messaging
   - Better feedback on alignment issues

## Implementation Notes

The objection generation feature is designed to critically challenge the user's thinking by presenting potential issues with the current project messaging. These objections are generated using the Claude API for each artifact type (project description, internal messaging, external messaging).

For new programmers: Each Python file has a specific purpose in the application. The structure follows a modular design where different aspects of functionality are separated into their own files and folders. This makes the code easier to understand, maintain, and extend.