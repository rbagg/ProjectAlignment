# Project Alignment Tool

A lightweight tool that keeps project documentation in sync and ensures alignment across all project artifacts.

## Purpose

The Project Alignment Tool serves two core functions:

1. **Documentation Synchronization**: Connects all project documentation (PRD, PRFAQ, strategy, tickets) and keeps everything updated when changes occur. When one document changes, it suggests updates to keep other documents aligned.

2. **Project Clarity**: Automatically generates three key artifacts:
   - **Project Description**: A concise 3-sentence and 3-paragraph explanation of what the project is, the customer pain point it's solving, and how it's being addressed.
   - **Internal Messaging**: Clear communication for internal teams about changes, their impact, and business value.
   - **External Messaging**: Customer-focused messaging explaining the pain point being solved and how the solution addresses it.

## Key Features

- **Bidirectional Change Tracking**: Detects changes in any connected document and suggests updates to keep everything aligned.
- **Artifact Generation**: Automatically creates and updates project descriptions and messaging.
- **Impact Analysis**: Evaluates if changes maintain project focus or indicate scope drift.
- **Minimal UI**: Simple, text-focused interface that prioritizes content and insights.

## Setup Instructions

### Prerequisites

- Python 3.7+
- Flask
- SQLAlchemy
- Access to external services (Google Docs, Jira, Linear, Confluence)

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

## Project Structure

```
app/
├── __init__.py
├── config.py
├── models/
│   ├── __init__.py
│   ├── version.py
│   ├── project.py
│   └── alignment.py
├── integrations/
│   ├── __init__.py
│   ├── google_docs.py
│   ├── jira.py
│   ├── linear.py
│   └── confluence.py
├── services/
│   ├── __init__.py
│   ├── sync_service.py
│   ├── alignment_service.py
│   ├── change_impact_analyzer.py
│   └── artifacts/
│       ├── __init__.py
│       ├── project_description.py
│       ├── internal_messaging.py
│       └── external_messaging.py
└── main.py
```

## Development Notes

- This project is designed to be lightweight and focused on alignment
- The UI is intentionally minimal to emphasize content
- Integration stubs need to be implemented with actual API calls

## License

[MIT License](LICENSE)