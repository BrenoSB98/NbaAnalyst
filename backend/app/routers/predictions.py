from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.db_utils import get_db
from app.db.models import Player, Team, Game, Prediction, PlayerGameStats
from app.config import config
from app.routers.auth import obter_usuario_atual
from app.services.prediction_service import prever_performance_jogador, prever_multiplas_stats_jogador
from app.services.manager_service import salvar_predicoes_dia_atual

router = APIRouter()

def _validar_jogador(db: Session, player_id: int) -> Player:
    jogador = db.query(Player).filter(Player.id == player_id).first()
    if not jogador:
        raise HTTPException(status_code=404, detail=f"Jogador {player_id} não encontrado.")
    return jogador

def _validar_time(db: Session, team_id: int) -> Team:
    time = db.query(Team).filter(Team.id == team_id).first()
    if not time:
        raise HTTPException(status_code=404, detail=f"Time {team_id} não encontrado.")
    return time

def _validar_jogo(db: Session, game_id: int) -> Game:
    jogo = db.query(Game).filter(Game.id == game_id).first()
    if not jogo:
        raise HTTPException(status_code=404, detail=f"Jogo {game_id} não encontrado.")
    return jogo

@router.get("/prever/jogador/{jogador_id}/vs/{time_adversario_id}")
def get_predicao(jogador_id: int, time_adversario_id: int, temporada: int, estatistica: str = Query(default="points"), eh_casa: int = Query(default=1, ge=0, le=1), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    jogador = _validar_jogador(db, jogador_id)
    time_adversario = _validar_time(db, time_adversario_id)
    if not time_adversario:
        raise HTTPException(status_code=404, detail="Time adversário não encontrado.")

    previsao = prever_performance_jogador(db, jogador_id, time_adversario_id, temporada, estatistica, eh_casa)

    return {
        "jogador": f"{jogador.firstname} {jogador.lastname}",
        "adversario": time_adversario.name,
        "temporada": temporada,
        "estatistica": estatistica,
        "is_home": eh_casa,
        "previsao": previsao,
    }

@router.get("/prever/jogador/{jogador_id}/vs/{time_adversario_id}/multiplas")
def get_predicao_multiplas(jogador_id: int, time_adversario_id: int, temporada: int, eh_casa: int = Query(default=1, ge=0, le=1), db: Session = Depends(get_db)):
    jogador = _validar_jogador(db, jogador_id)
    time_adversario = _validar_time(db, time_adversario_id)

    previsoes = prever_multiplas_stats_jogador(db, jogador_id, time_adversario_id, temporada, eh_casa)

    return {
        "jogador": f"{jogador.firstname} {jogador.lastname}",
        "adversario": time_adversario.name,
        "temporada": temporada,
        "is_home": eh_casa,
        "previsoes": previsoes,
    }

@router.get("/hoje")
def listar_predicoes_hoje(season: int = None, db: Session = Depends(get_db), ):
    if season:
        season_alvo = season
    else:
        season_alvo = config.NBA_SEASON

    agora = datetime.now(timezone.utc)
    inicio_do_dia = agora.replace(hour=0, minute=0, second=0, microsecond=0)
    fim_do_dia = inicio_do_dia + timedelta(days=1)

    jogos_hoje = (db.query(Game).filter(Game.season == season_alvo, Game.date_start >= inicio_do_dia, Game.date_start < fim_do_dia).all())

    if not jogos_hoje:
        return {"season": season_alvo, "data": str(agora.date()), "total_jogos": 0, "predicoes": []}

    ids_jogos_hoje = []
    for jogo in jogos_hoje:
        ids_jogos_hoje.append(jogo.id)

    predicoes = db.query(Prediction).filter(Prediction.game_id.in_(ids_jogos_hoje)).all()

    lista_resultado = []
    for pred in predicoes:
        jogador = db.query(Player).filter(Player.id == pred.player_id).first()
        nome_jogador = f"{jogador.firstname} {jogador.lastname}" if jogador else "Desconhecido"

        time = db.query(Team).filter(Team.id == pred.team_id).first()
        adversario = db.query(Team).filter(Team.id == pred.opponent_team_id).first()

        lista_resultado.append({
            "prediction_id": pred.id,
            "game_id": pred.game_id,
            "player_id": pred.player_id,
            "player_name": nome_jogador,
            "team_name": time.name if time else "Desconhecido",
            "opponent_name": adversario.name if adversario else "Desconhecido",
            "is_home": pred.is_home,
            "season": pred.season,
            "predicted_points": pred.predicted_points,
            "predicted_assists": pred.predicted_assists,
            "predicted_rebounds": pred.predicted_rebounds,
            "predicted_steals": pred.predicted_steals,
            "predicted_blocks": pred.predicted_blocks,
            "created_at": pred.created_at,
        })

    return {
        "season": season_alvo,
        "data": str(agora.date()),
        "total_jogos": len(jogos_hoje),
        "total_predicoes": len(lista_resultado),
        "predicoes": lista_resultado,
    }

@router.get("/jogo/{jogo_id}")
def listar_predicoes_por_jogo(jogo_id: int, db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    jogo = _validar_jogo(db, jogo_id)

    predicoes = db.query(Prediction).filter(Prediction.game_id == jogo_id).all()
    if not predicoes:
        return {"game_id": jogo_id, "total_predicoes": 0, "predicoes": []}

    time_casa = db.query(Team).filter(Team.id == jogo.home_team_id).first()
    time_visitante = db.query(Team).filter(Team.id == jogo.away_team_id).first()

    lista_resultado = []
    for pred in predicoes:
        jogador = db.query(Player).filter(Player.id == pred.player_id).first()
        if jogador:
            nome_jogador = f"{jogador.firstname} {jogador.lastname}" 
        else:
            nome_jogador = "Desconhecido"

        lista_resultado.append({
            "prediction_id": pred.id,
            "player_id": pred.player_id,
            "player_name": nome_jogador,
            "team_id": pred.team_id,
            "is_home": pred.is_home,
            "predicted_points": pred.predicted_points,
            "predicted_assists": pred.predicted_assists,
            "predicted_rebounds": pred.predicted_rebounds,
            "predicted_steals": pred.predicted_steals,
            "predicted_blocks": pred.predicted_blocks,
            "created_at": pred.created_at,
        })

    return {
        "game_id": jogo_id,
        "data_inicio": jogo.date_start,
        "time_casa": time_casa.name if time_casa else "Desconhecido",
        "time_visitante": time_visitante.name if time_visitante else "Desconhecido",
        "total_predicoes": len(lista_resultado),
        "predicoes": lista_resultado,
    }

@router.get("/jogador/{jogador_id}")
def listar_predicoes_por_jogador(jogador_id: int, temporada: int = None, limite: int = Query(default=10, ge=1, le=100), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    if temporada:
        temporada_alvo = temporada
    else:
        temporada_alvo = config.NBA_SEASON

    jogador = db.query(Player).filter(Player.id == jogador_id).first()
    if not jogador:
        raise HTTPException(status_code=404, detail=f"Jogador {jogador_id} não encontrado.")

    predicoes = (db.query(Prediction).filter(Prediction.player_id == jogador_id, Prediction.season == temporada_alvo)
                 .order_by(Prediction.created_at.desc()).limit(limite).all())

    lista_resultado = []
    for pred in predicoes:
        jogo = db.query(Game).filter(Game.id == pred.game_id).first()
        adversario = db.query(Team).filter(Team.id == pred.opponent_team_id).first()

        lista_resultado.append({
            "prediction_id": pred.id,
            "game_id": pred.game_id,
            "data_jogo": jogo.date_start if jogo else None,
            "adversario": adversario.name if adversario else "Desconhecido",
            "is_home": pred.is_home,
            "predicted_points": pred.predicted_points,
            "predicted_assists": pred.predicted_assists,
            "predicted_rebounds": pred.predicted_rebounds,
            "predicted_steals": pred.predicted_steals,
            "predicted_blocks": pred.predicted_blocks,
            "created_at": pred.created_at,
        })

    return {
        "player_id": jogador_id,
        "player_name": f"{jogador.firstname} {jogador.lastname}",
        "season": temporada_alvo,
        "total_predicoes": len(lista_resultado),
        "predicoes": lista_resultado,
    }

@router.post("/gerar/hoje")
def gerar_predicoes_hoje(temporada: int = None, db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    if temporada:
        temporada_alvo = temporada
    else:
        temporada_alvo = config.NBA_SEASON

    try:
        total = salvar_predicoes_dia_atual(db=db, season=temporada_alvo)
    except Exception as erro:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar predições: {str(erro)}")

    return {
        "mensagem": "Predições geradas com sucesso.",
        "season": temporada_alvo,
        "total_predicoes_geradas": total,
    }