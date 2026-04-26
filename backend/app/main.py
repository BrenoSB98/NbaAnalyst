import logging
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import config
from app.db.session import engine
from app.routers import api
from app.middleware.error_handler import tratar_erros_globais

logger = logging.getLogger("main")

app = FastAPI(
    title="NBA Analytics API",
    description="API para consulta de dados e estatísticas da NBA",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    redirect_slashes=False,
    contact={
        "name": "Breno Braido",
        "email": "bsbraido@gmail.com"
    },
)

ORIGENS_PERMITIDAS = [
    "http://localhost:3000",
    "http://localhost:5500",
    "http://localhost:8080",
    "http://127.0.0.1:5500",
    "http://127.0.0.1:8080",
]

app.middleware("http")(tratar_erros_globais)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENS_PERMITIDAS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.include_router(api.router, prefix="/api/v1", tags=["Main API"])

@app.get("/", tags=["Status"])
def ler_root():
    return {
        "api": "NBA Analytics API",
        "versao": "1.0.0",
        "status": "online",
        "docs": "/docs",
        "saude": "/saude",
    }

@app.get("/saude", tags=["Status"], summary="Verificação de saúde da API")
def saude_api():
    banco_status = "online"
    banco_detalhe = None

    try:
        with engine.connect() as conexao:
            conexao.execute(text("SELECT 1"))
    except Exception as erro:
        banco_status = "offline"
        banco_detalhe = str(erro)
        logger.error(f"Falha na verificação de saúde do banco de dados: {erro}")

    if banco_status == "online":
        status_geral = "saudavel"
    else:
        status_geral = "degradado"
        logger.warning("Verificação de saúde retornou status degradado: banco de dados offline.")

    resposta = {
        "status": status_geral,
        "versao": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "temporada_configurada": config.NBA_SEASON,
        "componentes": {
            "banco_de_dados": {"status": banco_status},
        },
    }

    if banco_detalhe:
        resposta["componentes"]["banco_de_dados"]["detalhe"] = banco_detalhe

    return resposta

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.BACKEND_HOST, port=config.BACKEND_PORT)