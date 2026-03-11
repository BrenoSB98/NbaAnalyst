import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import STATS_PERMITIDAS
from app.db.db_utils import get_db
from app.db.models import Player
from app.routers.auth import obter_usuario_admin
from app.services.backtest_service import backtest_jogador

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/jogador/{jogador_id}")
def get_backtest_jogador(jogador_id: int, temporada: int = Query(...), estatistica: str = Query(default="points"), ultimos_jogos: int = Query(default=10, ge=1, le=82),
                         db: Session = Depends(get_db), admin_atual=Depends(obter_usuario_admin)):
    if estatistica not in STATS_PERMITIDAS:
        raise HTTPException(status_code=400, detail=f"Estatística inválida. Escolha uma das opções: {STATS_PERMITIDAS}")

    jogador = db.query(Player).filter(Player.id == jogador_id).first()
    if not jogador:
        raise HTTPException(status_code=404, detail=f"Jogador {jogador_id} não encontrado.")

    resultado = backtest_jogador(db, jogador_id, temporada, estatistica, ultimos_jogos)
    if "error" in resultado:
        logger.warning(f"Backtest sem dados suficientes —> estatistica={estatistica}: {resultado['error']}")
        raise HTTPException(status_code=422, detail=resultado["error"])

    resultado["nome_jogador"] = f"{jogador.firstname} {jogador.lastname}"
    return resultado