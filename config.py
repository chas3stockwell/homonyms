import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
GAME_DURATION_SECONDS = 180  # 3 minutes
ALLOW_UNLIMITED_PLAYS = True  # Set to False to restrict to one play per day
CLAUDE_MODEL = "claude-sonnet-4-20250514"
