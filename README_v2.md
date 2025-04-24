# Project Alignment Tool

## Overview

Project Alignment Tool is an intelligent application that solves one of the most persistent challenges in software development - keeping project documentation synchronized and ensuring alignment across all project artifacts. It monitors changes in PRDs, tickets, and strategy documents, then suggests updates to maintain alignment, acting as a bridge between requirements and implementation.

With a minimalist, text-focused interface, Project Alignment Tool prioritizes content and insights over complex UI elements, making it accessible for all team members.

## Pain Points Addressed

Development teams struggle with documentation inconsistency that creates cascading problems:

* Engineers implement features based on outdated PRDs, resulting in misaligned deliverables
* Product managers update requirements without corresponding ticket updates, causing confusion
* Strategy changes aren't reflected in implementation plans, leading to missed business objectives
* Teams waste hours in meetings reconciling different versions of requirements
* Stakeholders lack clear messaging about what changes were made and why

These challenges compound in larger organizations where multiple stakeholders work across different tools and formats, creating a tangled web of misaligned documentation.

## Solution

Project Alignment Tool addresses these challenges through an integrated approach:

1. **Bidirectional Synchronization**: Connects with Google Docs (for PRDs/PRFAQs), Jira (for tickets), and Confluence (for strategy documents) to detect changes across your entire documentation ecosystem.

2. **Intelligent Change Detection**: Uses advanced analysis to identify when sections, requirements, or tickets are added, modified, or removed, understanding the significance of each change.

3. **Actionable Alignment Suggestions**: Provides specific recommendations to keep documentation in sync. When a PRD changes, it suggests what tickets should be updated. When tickets evolve, it recommends PRD modifications.

4. **Automated Artifact Generation**: Automatically creates and maintains:
   - **Project Descriptions**: Concise explanations of what the project is, pain points addressed, and solution approach
   - **Internal Messaging**: Clear communication for team members about project changes and their impact
   - **External Messaging**: Customer-focused communication highlighting benefits and value

5. **Change Impact Analysis**: Evaluates if changes maintain project focus or indicate scope drift, helping teams stay aligned with original objectives.

## Key Benefits

Using Project Alignment Tool provides significant advantages for development teams:

* **Reduced Miscommunication**: Everyone works from the same, up-to-date information, eliminating confusion and errors
* **Time Savings**: Eliminate hours spent reconciling different versions of documents and explaining inconsistencies
* **Improved Quality**: Fewer implementation errors due to documentation inconsistencies leads to better products
* **Stakeholder Alignment**: Clear, consistent messaging about the project and changes keeps everyone informed
* **Focus Maintenance**: Early detection of scope creep helps keep projects on track and within original parameters
* **Streamlined Communication**: Automatically generated artifacts for different audiences saves time and ensures consistency

## Getting Started

### Prerequisites

* Python 3.7+
* Flask and SQLAlchemy
* Claude API key (for enhanced content generation)
* Access to Google Docs, Jira, and/or Confluence

### Installation

1. **Clone the repository**
   ```
   git clone https://github.com/yourusername/project-alignment-tool.git
   cd project-alignment-tool
   ```

2. **Create a virtual environment**
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   - Create a `.env` file with the following variables:
   ```
   FLASK_APP=main.py
   FLASK_ENV=development

   # Claude API
   CLAUDE_API_KEY=your_claude_api_key

   # For Google Docs integration
   GOOGLE_CLIENT_ID=your_client_id
   GOOGLE_CLIENT_SECRET=your_client_secret

   # For Jira integration
   JIRA_API_KEY=your_jira_api_key
   JIRA_EMAIL=your_jira_email
   JIRA_DOMAIN=your_jira_domain

   # For Confluence integration
   CONFLUENCE_API_TOKEN=your_confluence_api_token
   CONFLUENCE_EMAIL=your_confluence_email
   CONFLUENCE_DOMAIN=your_confluence_domain
   ```

5. **Initialize the database**
   ```
   flask db init
   flask db migrate
   flask db upgrade
   ```

6. **Run the application**
   ```
   python main.py
   ```

### Basic Usage

1. **Connect your documents**
   - Visit the setup page at `/setup`
   - Link your Google Docs, Jira projects, and Confluence pages

2. **Monitor changes**
   - The system will automatically track changes in your connected documents
   - Visit the dashboard to see suggested updates

3. **Review artifacts**
   - The tool automatically generates project descriptions, internal and external messaging
   - Use these artifacts for team communication and customer updates

4. **Configure webhooks** (optional)
   - Set up webhooks in Jira, Confluence, etc., to enable real-time updates
   - Point them to the `/webhook` endpoint of your application

## Features

### Document Synchronization
- Bidirectional change tracking between PRDs, tickets, and strategy documents
- Real-time updates via webhooks from connected platforms
- Historical version tracking

### Alignment Analysis
- Intelligent detection of meaningful changes
- Impact analysis to evaluate if changes maintain project focus
- Actionable suggestions for maintaining alignment

### Artifact Generation
- Project descriptions in three sentences and three paragraphs
- Internal messaging for team communication
- External messaging for customer updates

### User Interface
- Minimalist, text-focused design
- Light background with dark text for readability
- Emphasis on content and insights

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.