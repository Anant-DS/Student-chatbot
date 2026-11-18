import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
ADMIN_KEY = os.getenv("ADMIN_KEY", "dev-admin-change-me")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-5-5")
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")]
RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))
MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", "0.12"))
TOKEN_MINUTES = 60
