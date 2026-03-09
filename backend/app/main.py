import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import api
from app.services.scheduler import iniciar_scheduler, encerrar_scheduler
from app.middleware.error_handler import tratar_erros_globais

logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    iniciar_scheduler()
    logger.info("Scheduler iniciado com sucesso.")
    yield
    encerrar_scheduler()
    logger.info("Scheduler encerrado com sucesso.")

app = FastAPI(
    title="NBA Analytics API",
    description="API para consulta de dados e estatísticas da NBA",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Breno Braido",
        "email": "bsbraido@gmail.com"
    },
    lifespan=lifespan
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.middleware("http")(tratar_erros_globais)
app.include_router(api.router, prefix="/api/v1", tags=["Main API"])

#@app.get("/")
#def ler_root():
#   return {"message": "NBA Analytics API is running"}

#@app.get("/saude", summary="Verificação de saúde da API")
#def saude_api():
#    return {
#        "status": "online",
#        "message": "NBA Analytics API está funcionando corretamente",
#        "version": "1.0.0"
#    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)