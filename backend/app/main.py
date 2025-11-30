from fastapi import FastAPI

from app.config import config
from app.routers import nba

app = FastAPI(title="NBA Score API")
app.include_router(nba.router)

@app.get("/health", tags=["health"])
def health_check():
    return {
        "status": "ok",
        "environment": config.BACKEND_ENV,
        "database_url": config.DATABASE_URL.replace(
            config.POSTGRES_PASSWORD,
            "***"
        ),
    }