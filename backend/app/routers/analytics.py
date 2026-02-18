from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.db_utils import get_db
from app.services.analytics import (
    buscar_top_pontuadores,
    buscar_top_assistencias,
    buscar_top_rebotes,
    buscar_top_roubos_bola,
    buscar_top_bloqueios,
    buscar_top_turnovers,
    buscar_top_arremessos_campo,
    buscar_top_arremessos_tres,
    buscar_top_lances_livres,
    buscar_top_rebotes_ofensivos,
    buscar_top_rebotes_defensivos,
    buscar_top_faltas_pessoais,
    buscar_top_plus_minus,
    calcular_medias_ultimos_n_jogos,
    calcular_medias_casa_fora,
    calcular_medias_temporada_completa,
    calcular_medias_contra_time
)
from app.db.models import Player, Team

router = APIRouter()

@router.get("/leaders/{season}/points")
def get_top_pontuadores(season: int, limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)):
    resultado = buscar_top_pontuadores(db, season, limit)
    if not resultado:
        return []
    return resultado


@router.get("/leaders/{season}/assists")
def get_top_assistencias(season: int, limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)):
    resultado = buscar_top_assistencias(db, season, limit)
    if not resultado:
        return []
    return resultado


@router.get("/leaders/{season}/rebounds")
def get_top_rebotes(season: int, limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)):
    resultado = buscar_top_rebotes(db, season, limit)
    if not resultado:
        return []
    return resultado


@router.get("/leaders/{season}/steals")
def get_top_roubos_bola(season: int, limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)):
    resultado = buscar_top_roubos_bola(db, season, limit)
    if not resultado:
        return []
    return resultado


@router.get("/leaders/{season}/blocks")
def get_top_bloqueios(season: int, limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)):
    resultado = buscar_top_bloqueios(db, season, limit)
    if not resultado:
        return []
    return resultado


@router.get("/leaders/{season}/turnovers")
def get_top_turnovers(season: int, limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)):
    resultado = buscar_top_turnovers(db, season, limit)
    if not resultado:
        return []
    return resultado


@router.get("/leaders/{season}/field_goals")
def get_top_arremessos_campo(season: int, limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)):
    resultado = buscar_top_arremessos_campo(db, season, limit)
    if not resultado:
        return []
    return resultado


@router.get("/leaders/{season}/three_points")
def get_top_arremessos_tres(season: int, limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)):
    resultado = buscar_top_arremessos_tres(db, season, limit)
    if not resultado:
        return []
    return resultado


@router.get("/leaders/{season}/free_throws")
def get_top_lances_livres(season: int, limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)):
    resultado = buscar_top_lances_livres(db, season, limit)
    if not resultado:
        return []
    return resultado


@router.get("/leaders/{season}/offensive_rebounds")
def get_top_rebotes_ofensivos(season: int, limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)):
    resultado = buscar_top_rebotes_ofensivos(db, season, limit)
    if not resultado:
        return []
    return resultado


@router.get("/leaders/{season}/defensive_rebounds")
def get_top_rebotes_defensivos(season: int, limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)):
    resultado = buscar_top_rebotes_defensivos(db, season, limit)
    if not resultado:
        return []
    return resultado


@router.get("/leaders/{season}/personal_fouls")
def get_top_faltas_pessoais(season: int, limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)):
    resultado = buscar_top_faltas_pessoais(db, season, limit)
    if not resultado:
        return []
    return resultado


@router.get("/leaders/{season}/plus_minus")
def get_top_plus_minus(season: int, limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)):
    resultado = buscar_top_plus_minus(db, season, limit)
    if not resultado:
        return []
    return resultado


@router.get("/players/{player_id}/stats/last_n_games")
def get_medias_ultimos_n_jogos(player_id: int, n_games: int = Query(default=10, ge=1, le=82), 
                                season: int = Query(default=None), db: Session = Depends(get_db)):
    jogador = db.query(Player).filter(Player.id == player_id).first()
    if not jogador:
        raise HTTPException(status_code=404, detail="Jogador nao encontrado")
    
    resultado = calcular_medias_ultimos_n_jogos(db, player_id, n_games, season)
    if not resultado:
        return {"message": "Nenhum dado encontrado"}
    
    resultado["player_id"] = player_id
    resultado["player_name"] = f"{jogador.firstname} {jogador.lastname}"
    return resultado


@router.get("/players/{player_id}/stats/home_away")
def get_medias_casa_fora(player_id: int, season: int, location: str = Query(default="home", regex="^(home|away)$"), 
                         db: Session = Depends(get_db)):
    jogador = db.query(Player).filter(Player.id == player_id).first()
    if not jogador:
        raise HTTPException(status_code=404, detail="Jogador nao encontrado")
    
    resultado = calcular_medias_casa_fora(db, player_id, season, location)
    if not resultado:
        return {"message": "Nenhum dado encontrado"}
    
    resultado["player_id"] = player_id
    resultado["player_name"] = f"{jogador.firstname} {jogador.lastname}"
    resultado["location"] = location
    resultado["season"] = season
    return resultado


@router.get("/players/{player_id}/stats/season")
def get_medias_temporada_completa(player_id: int, season: int, db: Session = Depends(get_db)):
    jogador = db.query(Player).filter(Player.id == player_id).first()
    if not jogador:
        raise HTTPException(status_code=404, detail="Jogador nao encontrado")
    
    resultado = calcular_medias_temporada_completa(db, player_id, season)
    if not resultado:
        return {"message": "Nenhum dado encontrado"}
    
    resultado["player_id"] = player_id
    resultado["player_name"] = f"{jogador.firstname} {jogador.lastname}"
    resultado["season"] = season
    return resultado


@router.get("/players/{player_id}/stats/vs_team/{opponent_team_id}")
def get_medias_contra_time(player_id: int, opponent_team_id: int, season: int = Query(default=None), 
                           db: Session = Depends(get_db)):
    jogador = db.query(Player).filter(Player.id == player_id).first()
    if not jogador:
        raise HTTPException(status_code=404, detail="Jogador nao encontrado")
    
    time_adversario = db.query(Team).filter(Team.id == opponent_team_id).first()
    if not time_adversario:
        raise HTTPException(status_code=404, detail="Time adversario nao encontrado")
    
    resultado = calcular_medias_contra_time(db, player_id, opponent_team_id, season)
    if not resultado:
        return {"message": "Nenhum dado encontrado"}
    
    resultado["player_id"] = player_id
    resultado["player_name"] = f"{jogador.firstname} {jogador.lastname}"
    resultado["opponent_team_id"] = opponent_team_id
    resultado["opponent_team_name"] = time_adversario.name
    if season:
        resultado["season"] = season
    return resultado
