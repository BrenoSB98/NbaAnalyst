from app.config import config

def print_config():
    print("=== Configurações Carregadas ===")
    print(f"POSTGRES_USER: {config.POSTGRES_USER}")
    print(f"POSTGRES_PASSWORD: {'***' if config.POSTGRES_PASSWORD else ''}")
    print(f"POSTGRES_DB: {config.POSTGRES_DB}")
    print(f"POSTGRES_HOST: {config.POSTGRES_HOST}")
    print(f"POSTGRES_PORT: {config.POSTGRES_PORT}")
    print(f"DATABASE_URL: {config.DATABASE_URL.replace(config.POSTGRES_PASSWORD, '***')}")

    print()
    print(f"API_SPORTS_BASE_URL: {config.API_SPORTS_BASE_URL}")
    print(f"API_SPORTS_KEY set: {bool(config.API_SPORTS_KEY)}")

    print()
    print(f"GEMINI_MODEL_NAME: {config.GEMINI_MODEL_NAME}")
    print(f"GEMINI_API_KEY set: {bool(config.GEMINI_API_KEY)}")

    print()
    print(f"OPENAI_MODEL_NAME: {config.OPENAI_MODEL_NAME}")
    print(f"OPENAI_API_KEY set: {bool(config.OPENAI_API_KEY)}")

    print()
    print(f"GROK_API_KEY set: {bool(config.GROK_API_KEY)}")
    
    print()
    print(f"BACKEND_ENV: {config.BACKEND_ENV}")
    print(f"LOG_LEVEL: {config.LOG_LEVEL}")

if __name__ == "__main__":
    print_config()