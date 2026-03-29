import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    NBA_SEASON = int(os.getenv("NBA_SEASON", "2025"))
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
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-5-mini")
    LIMITE_MENSAGENS_CHAT_DIA = int(os.getenv("LIMITE_MENSAGENS_CHAT_DIA", "20")) 
    LIMITE_MENSAGENS_CHAT = int(os.getenv("LIMITE_MENSAGENS_CHAT", "20"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    PROJETO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    SECRET_KEY = os.getenv("SECRET_KEY", "suasenha-secreta")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    
    MARGEM_PONTOS = float(os.getenv("MARGEM_PONTOS", "3.0"))
    MARGEM_ASSISTENCIAS = float(os.getenv("MARGEM_ASSISTENCIAS", "1.5"))
    MARGEM_REBOTES = float(os.getenv("MARGEM_REBOTES", "2.0"))
    MARGEM_ROUBOS = float(os.getenv("MARGEM_ROUBOS", "1.0"))
    MARGEM_BLOQUEIOS = float(os.getenv("MARGEM_BLOQUEIOS", "1.0"))
    
    MIN_MINUTOS_PALPITE = float(os.getenv("MIN_MINUTOS_PALPITE", "15.0"))
    
    PASTA_MODELOS = os.getenv("PASTA_MODELOS", "/opt/airflow/modelos_ml")
    
    
config = Config()