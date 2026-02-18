from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.db_utils import get_db
from app.services.prediction_service import prever_performance_jogador, prever_multiplas_stats_jogador
from app.services.backtest_service import executar_backtest_jogador
from app.db.models import Player, Team

router = APIRouter()

@router.get("/predict/player/{player_id}/vs/{opponent_team_id}")
def get_predicao_jogador(player_id: int, opponent_team_id: int, season: int, stat_name: str = Query(default="points"),
                         is_home: int = Query(default=1, ge=0, le=1), db: Session = Depends(get_db)):
    jogador = db.query(Player).filter(Player.id == player_id).first()
    if not jogador:
        raise HTTPException(status_code=404, detail="Jogador nao encontrado")
    
    time_adversario = db.query(Team).filter(Team.id == opponent_team_id).first()
    if not time_adversario:
        raise HTTPException(status_code=404, detail="Time adversario nao encontrado")
    
    previsao = prever_performance_jogador(db, player_id, opponent_team_id, season, stat_name, is_home)
    
    resultado = {
        "player_id": player_id,
        "player_name": f"{jogador.firstname} {jogador.lastname}",
        "opponent_team_id": opponent_team_id,
        "opponent_team_name": time_adversario.name,
        "season": season,
        "stat_name": stat_name,
        "is_home": is_home,
        "prediction": previsao
    }    
    return resultado

@router.get("/predict/player/{player_id}/vs/{opponent_team_id}/multiple")
def get_predicao_multiplas_stats(player_id: int, opponent_team_id: int, season: int, is_home: int = Query(default=1, ge=0, le=1), db: Session = Depends(get_db)):
    jogador = db.query(Player).filter(Player.id == player_id).first()
    if not jogador:
        raise HTTPException(status_code=404, detail="Jogador nao encontrado")
    
    time_adversario = db.query(Team).filter(Team.id == opponent_team_id).first()
    if not time_adversario:
        raise HTTPException(status_code=404, detail="Time adversario nao encontrado")
    
    previsoes = prever_multiplas_stats_jogador(db, player_id, opponent_team_id, season, is_home)
    
    resultado = {
        "player_id": player_id,
        "player_name": f"{jogador.firstname} {jogador.lastname}",
        "opponent_team_id": opponent_team_id,
        "opponent_team_name": time_adversario.name,
        "season": season,
        "is_home": is_home,
        "predictions": previsoes
    }
    return resultado

@router.get("/backtest/player/{player_id}")
def get_backtest_jogador(player_id: int, season: int, stat_name: str = "points", db: Session = Depends(get_db)):
    return executar_backtest_jogador(db, player_id, season, stat_name)