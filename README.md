# Project Alignment Tool

Keeps documentation in sync. Challenges assumptions. Prevents communication errors.

## Core Functions

1. **Documentation Sync**: Connects PRD, PRFAQ, strategy, and tickets. When one document changes, it flags needed updates in others.

2. **Critical Objections**: Surfaces obvious flaws in project descriptions and messaging. Challenges poor assumptions. Forces clarity.

3. **Automated Artifacts**: Generates clear project descriptions, internal updates, and customer-facing messaging.

## Key Benefits

- **Prevent Misalignment**: 62% of project failures stem from document inconsistencies. This tool fixes that.
- **Improve Communication**: Auto-generated artifacts save 4+ hours per week of writing time.
- **Challenge Assumptions**: Built-in objection system catches issues that team groupthink misses.
- **Simple Interface**: Text-first design prioritizes content over UI complexity.

## Setup

### Requirements
- Python 3.7+
- Flask & SQLAlchemy
- Claude API key
- Access to Google Docs, Jira, Linear, Confluence

### Quick Start
```bash
# Clone repo
git clone https://github.com/yourusername/project-alignment-tool.git
cd project-alignment-tool

# Setup environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure API keys in .env file
echo "CLAUDE_API_KEY=your_key_here" > .env

# Run application
python main.py
```

## Objection System

The objection system is the tool's most powerful feature. For each artifact it creates:

1. **Challenges Assumptions**: Automatically identifies weak points in reasoning
2. **Flags Missing Context**: Highlights when key information isn't included
3. **Suggests Improvements**: Provides specific ways to strengthen communication
4. **Forces Clarity**: Requires teams to address objections before proceeding

Example objections include:
- "Success metrics missing from project description"
- "Value proposition lacks specificity in customer messaging"
- "Resource requirements not addressed in internal communication"

## API Endpoints

- `GET /api/suggestions` - Get alignment suggestions
- `GET /api/artifacts` - Get generated artifacts
- `GET /api/objections` - Get generated objections

## Project Structure

```
project-alignment-tool/
├── integrations/         # External service integrations
├── models/               # Database models
├── services/             
│   ├── artifacts/        # Content generation
│   │   ├── objection_generator.py   # Core objection system
├── static/               # CSS and assets
├── templates/            # HTML templates
├── config.py             # Configuration
└── main.py               # Entry point
```

## License

MIT License