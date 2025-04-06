
# Project Architecture

```
project-alignment-tool/
│
├── integrations/                      # External service integrations
│   ├── __init__.py
│   ├── confluence.py                  # Confluence API integration
│   ├── google_docs.py                 # Google Docs API integration
│   └── jira.py                        # Jira API integration
│
├── models/                            # Database models
│   ├── __init__.py                   # Database initialization
│   ├── alignment.py                   # Alignment model for suggestions
│   └── project.py                     # Project model for content storage
│
├── services/                          # Core business logic
│   ├── artifacts/                     # Content generation services
│   │   ├── __init__.py
│   │   ├── external_messaging.py      # Customer-facing message generator
│   │   ├── internal_messaging.py      # Team communication generator
│   │   └── project_description.py     # Project summary generator
│   │
│   ├── alignment_service.py           # Alignment analysis service
│   ├── change_impact_analyzer.py      # Change impact evaluation
│   └── sync_service.py                # Document synchronization
│
├── static/                            # Static assets
│   └── (CSS, JS, images)
│
├── templates/                         # HTML templates
│   ├── base.html                      # Base template layout
│   ├── index.html                     # Main dashboard
│   ├── setup.html                     # Integration setup
│   ├── test.html                      # Testing interface
│   └── test_results.html              # Test generation results
│
├── .gitignore                         # Git ignore rules
├── .replit                            # Replit configuration
├── README.md                          # Project documentation
├── config.py                          # Application configuration
├── main.py                            # Application entry point
├── requirements.txt                   # Python dependencies
└── uv.lock                            # Dependency lock file
```
