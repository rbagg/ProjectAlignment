# Project Alignment Tool

A lightweight tool that keeps project documentation in sync, ensures alignment across all project artifacts, and challenges thinking with critical objections.

## Purpose

The Project Alignment Tool serves three core functions:

1. **Documentation Synchronization**: Connects all project documentation (PRD, PRFAQ, strategy, tickets) and keeps everything updated when changes occur. When one document changes, it suggests updates to keep other documents aligned.

2. **Project Clarity**: Automatically generates three key artifacts:
   - **Project Description**: A concise 3-sentence and 3-paragraph explanation of what the project is, the customer pain point it's solving, and how it's being addressed.
   - **Internal Messaging**: Clear communication for internal teams about changes, their impact, and business value.
   - **External Messaging**: Customer-focused messaging explaining the pain point being solved and how the solution addresses it.

3. **Critical Thinking**: Generates thoughtful objections to challenge assumptions, identify blind spots, and improve the quality of project communications by considering alternative perspectives.

## Key Features

- **Bidirectional Change Tracking**: Detects changes in any connected document and suggests updates to keep everything aligned.
- **Artifact Generation**: Automatically creates and updates project descriptions and messaging.
- **Objection Generation**: Identifies potential issues and challenges in the generated content to encourage critical thinking.
- **Impact Analysis**: Evaluates if changes maintain project focus or indicate scope drift.
- **Minimal UI**: Simple, text-focused interface that prioritizes content and insights.

## Setup Instructions

### Prerequisites

- Python 3.7+
- Flask
- SQLAlchemy
- Access to external services (Google Docs, Jira, Linear, Confluence)
- Claude API key (for content generation)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/project-alignment-tool.git
   cd project-alignment-tool
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   - Create a `.env` file with the following variables:
     ```
     FLASK_APP=main.py
     FLASK_ENV=development

     # Claude API 
     CLAUDE_API_KEY=your_anthropic_api_key
     CLAUDE_MODEL=claude-3-opus-20240229

     # For Google Docs integration
     GOOGLE_CLIENT_ID=your_client_id
     GOOGLE_CLIENT_SECRET=your_client_secret

     # For Jira integration
     JIRA_API_KEY=your_jira_api_key
     JIRA_EMAIL=your_jira_email
     JIRA_DOMAIN=your_jira_domain

     # For Linear integration
     LINEAR_API_KEY=your_linear_api_key

     # For Confluence integration
     CONFLUENCE_API_TOKEN=your_confluence_api_token
     CONFLUENCE_EMAIL=your_confluence_email
     CONFLUENCE_DOMAIN=your_confluence_domain
     ```

5. Initialize the database:
   ```
   flask db init
   flask db migrate
   flask db upgrade
   ```

6. Run the application:
   ```
   python main.py
   ```

### Connecting Documents

1. Visit the setup page at `/setup`
2. Authenticate with Google to connect Google Docs
3. Connect your project documentation:
   - PRD (Google Doc)
   - PRFAQ (Google Doc)
   - Strategy (Google Doc or Confluence)
   - Tickets (Jira or Linear)

### Webhooks Configuration

To enable real-time updates, configure webhooks in your connected services to point to:

- Jira: `http://your-domain.com/webhook`
- Linear: `http://your-domain.com/webhook`
- Google Docs: Configure the Google Drive API push notifications
- Confluence: Configure webhooks in Confluence admin

## Using the Critical Objections Feature

The Project Alignment Tool now automatically generates thoughtful objections for each artifact it creates:

1. **Project Description Objections**: Challenges assumptions about the problem definition, solution approach, and implementation realities.

2. **Internal Messaging Objections**: Identifies potential issues with resource requirements, success metrics, and change management needs that might be overlooked.

3. **External Messaging Objections**: Surfaces potential customer concerns, competitive differentiation issues, and value proposition clarity.

These objections are designed to:
- Challenge core assumptions
- Identify potential blind spots
- Suggest alternative perspectives
- Improve the overall quality of communication

By considering these objections, you can strengthen your project communications and preemptively address potential issues.

## API Endpoints

The application provides several API endpoints:

- `GET /api/suggestions` - Get latest alignment suggestions
- `GET /api/artifacts` - Get all generated artifacts
- `GET /api/objections` - Get all generated objections

## Project Structure

```
project-alignment-tool/
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
│   ├── index.html                     # Main dashboard
│   ├── setup.html                     # Integration setup
│   ├── test.html                      # Testing interface
│   └── test_results.html              # Test generation results
│
├── config.py                          # Application configuration
├── main.py                            # Application entry point
├── requirements.txt                   # Python dependencies
└── README.md                          # This documentation
```

## Development Notes

- This project uses the Claude API for generating content, objections, and analyzing changes
- The UI is intentionally minimal to emphasize content and insights
- The integration modules provide mock implementations that should be replaced with actual API calls
- The objection generator provides alternative perspectives to encourage critical thinking

## License

[MIT License](LICENSE)