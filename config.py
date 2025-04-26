# config.py
import os
from datetime import timedelta

class Config:
    """Application configuration"""
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-for-project-alignment-tool')
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)

    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///project_alignment.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Claude API settings - directly use environment variable if available
    CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY')
    CLAUDE_MODEL = os.environ.get('CLAUDE_MODEL', 'claude-3-opus-20240229')

    # API keys and credentials (to be set in environment variables)
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    JIRA_API_KEY = os.environ.get('JIRA_API_KEY')
    JIRA_EMAIL = os.environ.get('JIRA_EMAIL')
    JIRA_DOMAIN = os.environ.get('JIRA_DOMAIN')
    CONFLUENCE_API_TOKEN = os.environ.get('CONFLUENCE_API_TOKEN')
    CONFLUENCE_EMAIL = os.environ.get('CONFLUENCE_EMAIL')
    CONFLUENCE_DOMAIN = os.environ.get('CONFLUENCE_DOMAIN')

    def __init__(self):
        """Initialize config with additional environment checks"""
        # Check for Replit secrets format (might be prefixed)
        if not self.CLAUDE_API_KEY and 'REPLIT_CLAUDE_API_KEY' in os.environ:
            self.CLAUDE_API_KEY = os.environ.get('REPLIT_CLAUDE_API_KEY')

        # Check for secrets file (older Replit versions)
        if not self.CLAUDE_API_KEY and os.path.exists('/run/secrets/CLAUDE_API_KEY'):
            try:
                with open('/run/secrets/CLAUDE_API_KEY', 'r') as f:
                    self.CLAUDE_API_KEY = f.read().strip()
            except Exception as e:
                print(f"Error reading from secrets file: {e}")