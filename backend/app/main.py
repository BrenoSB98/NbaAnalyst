import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import config
from app.db.session import engine
from app.routers import api
from app.services.scheduler import iniciar_scheduler, encerrar_scheduler, scheduler
from app.middleware.error_handler import tratar_erros_globais

logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        iniciar_scheduler()
        logger.warning("Scheduler iniciado.")
    except Exception as erro:
        logger.error(f"Falha ao iniciar o scheduler: {erro}")
    yield
    try:
        encerrar_scheduler()
        logger.warning("Scheduler encerrado com sucesso.")
    except Exception as erro:
        logger.error(f"Falha ao encerrar o scheduler: {erro}")
 
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
    lifespan=lifespan
)
 
app.middleware("http")(tratar_erros_globais)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]) 
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
 
    if scheduler.running:
        scheduler_status = "rodando"
    else:
        scheduler_status = "parado"
 
    if banco_status == "online" and scheduler_status == "rodando":
        status_geral = "saudavel"
    elif banco_status == "offline":
        status_geral = "degradado"
        logger.warning("Verificação de saúde retornou status degradado —> banco de dados offline.")
    else:
        status_geral = "parcial"
        logger.warning(f"Verificação de saúde retornou status parcial —> scheduler={scheduler_status}.")
 
    resposta = {
        "status": status_geral,
        "versao": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "temporada_configurada": config.NBA_SEASON,
        "componentes": {
            "banco_de_dados": {"status": banco_status},
            "scheduler": {"status": scheduler_status},
        },
    }
 
    if banco_detalhe:
        resposta["componentes"]["banco_de_dados"]["detalhe"] = banco_detalhe
    return resposta
 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.BACKEND_HOST, port=config.BACKEND_PORT)