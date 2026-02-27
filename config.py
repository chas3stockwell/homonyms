import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
CLAUDE_MODEL = "claude-haiku-4-5-20251001"
GAME_DURATION_SECONDS = 180  # 3 minutes
ALLOW_UNLIMITED_PLAYS = True  # Set to False to restrict to one play per day
