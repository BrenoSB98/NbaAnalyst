from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.models import Player
from app.db.db_utils import get_db
from app.services.backtest_service import backtest_jogador
from app.routers.auth import obter_usuario_admin

router = APIRouter()
STATS_PERMITIDAS = ["points", "assists", "tot_reb", "steals", "blocks", "turnovers"]

@router.get("/jogador/{jogador_id}")
def get_backtest_jogador(jogador_id: int, temporada: int = Query(...), estatistica: str = Query(default="points"), ultimos_jogos: int = Query(default=10, ge=1, le=82), db: Session = Depends(get_db),
    admin_atual=Depends(obter_usuario_admin)):
    if estatistica not in STATS_PERMITIDAS:
        raise HTTPException(status_code=400, detail=f"Estatística inválida. Escolha uma das opções: {STATS_PERMITIDAS}")

    jogador = db.query(Player).filter(Player.id == jogador_id).first()
    if not jogador:
        raise HTTPException(status_code=404, detail=f"Jogador {jogador_id} não encontrado.")

    resultado = backtest_jogador(db, jogador_id, temporada, estatistica, ultimos_jogos)

    if "error" in resultado:
        raise HTTPException(status_code=422, detail=resultado["error"])

    resultado["nome_jogador"] = f"{jogador.firstname} {jogador.lastname}"
    return resultado