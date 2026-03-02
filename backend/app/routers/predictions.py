from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.db_utils import get_db
from app.db.models import Player, Team, Game, Prediction, PlayerGameStats
from app.config import config
from app.services.prediction_service import prever_performance_jogador, prever_multiplas_stats_jogador
from app.services.manager_service import salvar_predicoes_dia_atual

router = APIRouter()

@router.get("/prever/jogador/{player_id}/vs/{opponent_team_id}")
def get_predicao(player_id: int, opponent_team_id: int, season: int, stat_name: str = Query(default="points"), is_home: int = Query(default=1, ge=0, le=1), db: Session = Depends(get_db)):
    jogador = db.query(Player).filter(Player.id == player_id).first()
    if not jogador:
        raise HTTPException(status_code=404, detail="Jogador não encontrado.")

    time_adversario = db.query(Team).filter(Team.id == opponent_team_id).first()
    if not time_adversario:
        raise HTTPException(status_code=404, detail="Time adversário não encontrado.")

    previsao = prever_performance_jogador(db, player_id, opponent_team_id, season, stat_name, is_home)

    return {
        "jogador": f"{jogador.firstname} {jogador.lastname}",
        "adversario": time_adversario.name,
        "temporada": season,
        "estatistica": stat_name,
        "is_home": is_home,
        "previsao": previsao,
    }

@router.get("/prever/jogador/{player_id}/vs/{opponent_team_id}/multiplas")
def get_predicao_multiplas(player_id: int, opponent_team_id: int, season: int, is_home: int = Query(default=1, ge=0, le=1), db: Session = Depends(get_db)):
    jogador = db.query(Player).filter(Player.id == player_id).first()
    if not jogador:
        raise HTTPException(status_code=404, detail="Jogador não encontrado.")

    time_adversario = db.query(Team).filter(Team.id == opponent_team_id).first()
    if not time_adversario:
        raise HTTPException(status_code=404, detail="Time adversário não encontrado.")

    previsoes = prever_multiplas_stats_jogador(db, player_id, opponent_team_id, season, is_home)

    return {
        "jogador": f"{jogador.firstname} {jogador.lastname}",
        "adversario": time_adversario.name,
        "temporada": season,
        "is_home": is_home,
        "previsoes": previsoes,
    }

@router.get("/backtest/jogador/{player_id}")
def get_backtest_jogador(player_id: int, season: int, stat_name: str = Query(default="points"), db: Session = Depends(get_db)):
    jogador = db.query(Player).filter(Player.id == player_id).first()
    if not jogador:
        raise HTTPException(status_code=404, detail="Jogador não encontrado.")

    jogos_query = (db.query(PlayerGameStats, Game).join(Game, PlayerGameStats.game_id == Game.id)
                   .filter(PlayerGameStats.player_id == player_id, Game.season == season, Game.status_short == 3)
                   .order_by(Game.date_start).all())

    if len(jogos_query) < 6:
        raise HTTPException(status_code=400, detail="Jogador não possui jogos suficientes para backtest.")

    resultados_backtest = []
    erros_totais = 0
    soma_erros_absolutos = 0.0

    for i in range(5, len(jogos_query)):
        stat_atual = jogos_query[i][0]
        jogo_atual = jogos_query[i][1]

        if jogo_atual.home_team_id == stat_atual.team_id:
            is_home = 1
        else:
            is_home = 0

        if is_home == 1:
            adversario_id = jogo_atual.away_team_id
        else:
            adversario_id = jogo_atual.home_team_id

        try:
            valor_previsto = prever_performance_jogador(db, player_id, adversario_id, season, stat_name, is_home)
        except Exception:
            continue

        valor_real = float(getattr(stat_atual, stat_name, 0) or 0)
        erro_absoluto = abs(valor_previsto - valor_real)
        soma_erros_absolutos = soma_erros_absolutos + erro_absoluto
        erros_totais = erros_totais + 1

        resultados_backtest.append({
            "jogo_id": jogo_atual.id,
            "data_jogo": jogo_atual.date_start,
            "previsao": valor_previsto,
            "real": valor_real,
            "erro_absoluto": round(erro_absoluto, 2),
        })

    mae = None
    if erros_totais > 0:
        mae = round(soma_erros_absolutos / erros_totais, 2)

    return {
        "jogador": f"{jogador.firstname} {jogador.lastname}",
        "temporada": season,
        "estatistica": stat_name,
        "total_testes": erros_totais,
        "media_erro_absoluto": mae,
        "resultados": resultados_backtest,
    }

@router.get("/hoje")
def listar_predicoes_hoje(season: int = None, db: Session = Depends(get_db)):
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

@router.get("/jogo/{game_id}")
def listar_predicoes_por_jogo(game_id: int, db: Session = Depends(get_db)):
    jogo = db.query(Game).filter(Game.id == game_id).first()
    if not jogo:
        raise HTTPException(status_code=404, detail=f"Jogo {game_id} não encontrado.")

    predicoes = db.query(Prediction).filter(Prediction.game_id == game_id).all()
    if not predicoes:
        return {"game_id": game_id, "total_predicoes": 0, "predicoes": []}

    time_casa = db.query(Team).filter(Team.id == jogo.home_team_id).first()
    time_visitante = db.query(Team).filter(Team.id == jogo.away_team_id).first()

    lista_resultado = []
    for pred in predicoes:
        jogador = db.query(Player).filter(Player.id == pred.player_id).first()
        nome_jogador = f"{jogador.firstname} {jogador.lastname}" if jogador else "Desconhecido"

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
        "game_id": game_id,
        "data_inicio": jogo.date_start,
        "time_casa": time_casa.name if time_casa else "Desconhecido",
        "time_visitante": time_visitante.name if time_visitante else "Desconhecido",
        "total_predicoes": len(lista_resultado),
        "predicoes": lista_resultado,
    }

@router.get("/jogador/{player_id}")
def listar_predicoes_por_jogador(player_id: int, season: int = None, limit: int = Query(default=10, ge=1, le=100), db: Session = Depends(get_db)):
    if season:
        season_alvo = season
    else:
        season_alvo = config.NBA_SEASON

    jogador = db.query(Player).filter(Player.id == player_id).first()
    if not jogador:
        raise HTTPException(status_code=404, detail=f"Jogador {player_id} não encontrado.")

    predicoes = (db.query(Prediction).filter(Prediction.player_id == player_id, Prediction.season == season_alvo)
                 .order_by(Prediction.created_at.desc()).limit(limit).all())

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
        "player_id": player_id,
        "player_name": f"{jogador.firstname} {jogador.lastname}",
        "season": season_alvo,
        "total_predicoes": len(lista_resultado),
        "predicoes": lista_resultado,
    }

@router.post("/gerar/hoje")
def gerar_predicoes_hoje(season: int = None, db: Session = Depends(get_db)):
    if season:
        season_alvo = season
    else:
        season_alvo = config.NBA_SEASON

    try:
        total = salvar_predicoes_dia_atual(db=db, season=season_alvo)
    except Exception as erro:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar predições: {str(erro)}")

    return {
        "mensagem": "Predições geradas com sucesso.",
        "season": season_alvo,
        "total_predicoes_geradas": total,
    }