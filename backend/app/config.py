import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    POSTGRES_USER = os.getenv("POSTGRES_USER", "admin")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "nba_score_db")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

    DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

    API_SPORTS_KEY = os.getenv("API_SPORTS_KEY", "")
    API_SPORTS_BASE_URL = os.getenv("API_SPORTS_BASE_URL", "https://v2.nba.api-sports.io")

    BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
    BACKEND_ENV = os.getenv("BACKEND_ENV", "development")

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-pro")

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")

    GROK_API_KEY = os.getenv("GROK_API_KEY", "")

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

config = Config()