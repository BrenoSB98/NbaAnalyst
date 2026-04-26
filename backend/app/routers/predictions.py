import logging
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import obter_temporada
from app.db.db_utils import get_db
from app.db.models import Game, Player, PlayerGameStats, Prediction, Team
from app.routers.auth import obter_usuario_atual
from app.services.manager_service import salvar_predicoes_dia_atual, salvar_predicoes_temporada
from app.services.prediction_service import prever_performance_jogador, prever_multiplas_stats_jogador
from app.services.formatar_palpites import formatar_palpite

router = APIRouter()
logger = logging.getLogger(__name__)

def _validar_jogador(db, player_id):
    jogador = db.query(Player).filter(Player.id == player_id).first()
    if not jogador:
        raise HTTPException(status_code=404, detail=f"Jogador {player_id} não encontrado.")
    return jogador

def _validar_time(db, team_id):
    time = db.query(Team).filter(Team.id == team_id).first()
    if not time:
        raise HTTPException(status_code=404, detail=f"Time {team_id} não encontrado.")
    return time

def _validar_jogo(db, game_id):
    jogo = db.query(Game).filter(Game.id == game_id).first()
    if not jogo:
        raise HTTPException(status_code=404, detail=f"Jogo {game_id} não encontrado.")
    return jogo

@router.get("/prever/jogador/{jogador_id}/vs/{time_adversario_id}")
def get_predicao(jogador_id: int, time_adversario_id: int, temporada: int = Query(...), estatistica: str = Query(default="points"), eh_casa: int = Query(default=1, ge=0, le=1), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    jogador = _validar_jogador(db, jogador_id)
    time_adversario = _validar_time(db, time_adversario_id)

    previsao = prever_performance_jogador(db, jogador_id, time_adversario_id, temporada, estatistica, eh_casa)

    return {
        "jogador_id": jogador_id,
        "jogador": f"{jogador.firstname} {jogador.lastname}",
        "adversario_id": time_adversario_id,
        "adversario": time_adversario.name,
        "temporada": temporada,
        "estatistica": estatistica,
        "eh_casa": eh_casa,
        "previsao": previsao,
    }

@router.get("/prever/jogador/{jogador_id}/vs/{time_adversario_id}/multiplas")
def get_predicao_multiplas(jogador_id: int, time_adversario_id: int, temporada: int = Query(...), eh_casa: int = Query(default=1, ge=0, le=1), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    jogador = _validar_jogador(db, jogador_id)
    time_adversario = _validar_time(db, time_adversario_id)

    previsoes = prever_multiplas_stats_jogador(db, jogador_id, time_adversario_id, temporada, eh_casa)

    return {
        "jogador_id": jogador_id,
        "jogador": f"{jogador.firstname} {jogador.lastname}",
        "adversario_id": time_adversario_id,
        "adversario": time_adversario.name,
        "temporada": temporada,
        "eh_casa": eh_casa,
        "previsoes": previsoes,
    }

@router.get("/contagem-hoje")
def contar_palpites_hoje(temporada_alvo: int = Depends(obter_temporada), db: Session = Depends(get_db)):
    fuso_sp = ZoneInfo("America/Sao_Paulo")
    agora_sp = datetime.now(fuso_sp)
    inicio_sp = agora_sp.replace(hour=0, minute=0, second=0, microsecond=0)
    fim_sp = inicio_sp + timedelta(days=1, hours=6)
    inicio_utc = inicio_sp.astimezone(timezone.utc)
    fim_utc = fim_sp.astimezone(timezone.utc)
 
    jogos_hoje = db.query(Game).filter(Game.season == temporada_alvo, Game.date_start >= inicio_utc, Game.date_start < fim_utc).all() 
    if not jogos_hoje:
        return {"total_palpites": 0} 
    ids_jogos = []
    for jogo in jogos_hoje:
        ids_jogos.append(jogo.id) 
    total = db.query(Prediction).filter(Prediction.game_id.in_(ids_jogos)).count() 
    return {"total_palpites": total}

@router.get("/hoje")
def listar_predicoes_hoje(temporada_alvo: int = Depends(obter_temporada), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    fuso_sp = ZoneInfo("America/Sao_Paulo")
    agora_sp = datetime.now(fuso_sp)
    inicio_sp = agora_sp.replace(hour=0, minute=0, second=0, microsecond=0)
    fim_sp = inicio_sp + timedelta(days=1, hours=6)
    inicio_utc = inicio_sp.astimezone(timezone.utc)
    fim_utc = fim_sp.astimezone(timezone.utc)

    jogos_hoje = db.query(Game).filter(Game.season == temporada_alvo, Game.date_start >= inicio_utc, Game.date_start < fim_utc).all()

    if not jogos_hoje:
        return {"temporada": temporada_alvo, "data": str(agora_sp.date()), "total_jogos": 0, "total_predicoes": 0, "predicoes": []}

    ids_jogos_hoje = []
    for jogo in jogos_hoje:
        ids_jogos_hoje.append(jogo.id)

    predicoes = db.query(Prediction).filter(Prediction.game_id.in_(ids_jogos_hoje)).all()

    # Busca jogos na temporada de cada jogador em batch para evitar N+1
    ids_players = []
    for pred in predicoes:
        ids_players.append(pred.player_id)

    contagem_jogos_map = {}
    rows_contagem = (
        db.query(PlayerGameStats.player_id, func.count(PlayerGameStats.game_id).label("total"))
        .join(Game, PlayerGameStats.game_id == Game.id)
        .filter(PlayerGameStats.player_id.in_(ids_players), Game.season == temporada_alvo, Game.status_short == 3, Game.stage != 1)
        .group_by(PlayerGameStats.player_id)
        .all()
    )
    for row in rows_contagem:
        contagem_jogos_map[row[0]] = row[1]

    medias_map = {}
    rows_medias = db.query(PlayerGameStats.player_id, func.avg(PlayerGameStats.points).label("avg_pts"), func.avg(PlayerGameStats.assists).label("avg_ast"), func.avg(PlayerGameStats.tot_reb).label("avg_reb"), func.avg(PlayerGameStats.steals).label("avg_stl"), func.avg(PlayerGameStats.blocks).label("avg_blk")).join(Game, PlayerGameStats.game_id == Game.id).filter(PlayerGameStats.player_id.in_(ids_players), Game.season == temporada_alvo, Game.status_short == 3, Game.stage != 1).group_by(PlayerGameStats.player_id).all()

    for row in rows_medias:
        medias_map[row[0]] = {}
        medias_map[row[0]]["pontos"] = round(float(row.avg_pts or 0), 2)
        medias_map[row[0]]["assistencias"] = round(float(row.avg_ast or 0), 2)
        medias_map[row[0]]["rebotes"] = round(float(row.avg_reb or 0), 2)
        medias_map[row[0]]["roubos"] = round(float(row.avg_stl or 0), 2)
        medias_map[row[0]]["bloqueios"] = round(float(row.avg_blk or 0), 2)

    lista_resultado = []
    for pred in predicoes:
        jogador = db.query(Player).filter(Player.id == pred.player_id).first()
        if jogador:
            nome_jogador = f"{jogador.firstname} {jogador.lastname}"
        else:
            nome_jogador = "Desconhecido"

        time = db.query(Team).filter(Team.id == pred.team_id).first()
        adversario = db.query(Team).filter(Team.id == pred.opponent_team_id).first()

        palpite_pts = formatar_palpite(pred.predicted_points)
        palpite_ast = formatar_palpite(pred.predicted_assists)
        palpite_reb = formatar_palpite(pred.predicted_rebounds)
        palpite_stl = formatar_palpite(pred.predicted_steals)
        palpite_blk = formatar_palpite(pred.predicted_blocks)

        jogos_na_temporada = contagem_jogos_map.get(pred.player_id, 0)
        medias_jogador = medias_map.get(pred.player_id, {})

        item_resultado = {}
        item_resultado["prediction_id"] = pred.id
        item_resultado["game_id"] = pred.game_id
        item_resultado["player_id"] = pred.player_id
        item_resultado["nome_jogador"] = nome_jogador
        item_resultado["nome_time"] = time.name if time else "Desconhecido"
        item_resultado["nome_adversario"] = adversario.name if adversario else "Desconhecido"
        item_resultado["eh_casa"] = pred.is_home
        item_resultado["temporada"] = pred.season
        item_resultado["pontos_previstos"] = pred.predicted_points
        item_resultado["assistencias_previstas"] = pred.predicted_assists
        item_resultado["rebotes_previstos"] = pred.predicted_rebounds
        item_resultado["roubos_previstos"] = pred.predicted_steals
        item_resultado["bloqueios_previstos"] = pred.predicted_blocks
        item_resultado["media_pontos"] = medias_jogador.get("pontos", 0.0)
        item_resultado["media_assistencias"] = medias_jogador.get("assistencias", 0.0)
        item_resultado["media_rebotes"] = medias_jogador.get("rebotes", 0.0)
        item_resultado["media_roubos"] = medias_jogador.get("roubos", 0.0)
        item_resultado["media_bloqueios"] = medias_jogador.get("bloqueios", 0.0)
        item_resultado["palpite_pontos"] = palpite_pts
        item_resultado["palpite_assistencias"] = palpite_ast
        item_resultado["palpite_rebotes"] = palpite_reb
        item_resultado["palpite_roubos"] = palpite_stl
        item_resultado["palpite_bloqueios"] = palpite_blk
        item_resultado["jogos_na_temporada"] = jogos_na_temporada
        item_resultado["criado_em"] = pred.created_at
        lista_resultado.append(item_resultado)

    return {
        "temporada": temporada_alvo,
        "data": str(agora_sp.date()),
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

        palpite_pts = formatar_palpite(pred.predicted_points)
        palpite_ast = formatar_palpite(pred.predicted_assists)
        palpite_reb = formatar_palpite(pred.predicted_rebounds)
        palpite_stl = formatar_palpite(pred.predicted_steals)
        palpite_blk = formatar_palpite(pred.predicted_blocks)

        lista_resultado.append({
            "prediction_id": pred.id,
            "player_id": pred.player_id,
            "nome_jogador": nome_jogador,
            "team_id": pred.team_id,
            "eh_casa": pred.is_home,
            "pontos_previstos": pred.predicted_points,
            "assistencias_previstas": pred.predicted_assists,
            "rebotes_previstos": pred.predicted_rebounds,
            "roubos_previstos": pred.predicted_steals,
            "bloqueios_previstos": pred.predicted_blocks,
            "palpite_pontos": palpite_pts,
            "palpite_assistencias": palpite_ast,
            "palpite_rebotes": palpite_reb,
            "palpite_roubos": palpite_stl,
            "palpite_bloqueios": palpite_blk,
            "criado_em": pred.created_at,
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
def listar_predicoes_por_jogador(jogador_id: int, temporada_alvo: int = Depends(obter_temporada), limite: int = Query(default=10, ge=1, le=100), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    jogador = _validar_jogador(db, jogador_id)
    predicoes = db.query(Prediction).filter(Prediction.player_id == jogador_id, Prediction.season == temporada_alvo).order_by(Prediction.created_at.desc()).limit(limite).all()

    lista_resultado = []
    for pred in predicoes:
        jogo = db.query(Game).filter(Game.id == pred.game_id).first()
        adversario = db.query(Team).filter(Team.id == pred.opponent_team_id).first()

        palpite_pts = formatar_palpite(pred.predicted_points)
        palpite_ast = formatar_palpite(pred.predicted_assists)
        palpite_reb = formatar_palpite(pred.predicted_rebounds)
        palpite_stl = formatar_palpite(pred.predicted_steals)
        palpite_blk = formatar_palpite(pred.predicted_blocks)

        lista_resultado.append({
            "prediction_id": pred.id,
            "game_id": pred.game_id,
            "data_jogo": jogo.date_start if jogo else None,
            "adversario": adversario.name if adversario else "Desconhecido",
            "eh_casa": pred.is_home,
            "pontos_previstos": pred.predicted_points,
            "assistencias_previstas": pred.predicted_assists,
            "rebotes_previstos": pred.predicted_rebounds,
            "roubos_previstos": pred.predicted_steals,
            "bloqueios_previstos": pred.predicted_blocks,
            "palpite_pontos": palpite_pts,
            "palpite_assistencias": palpite_ast,
            "palpite_rebotes": palpite_reb,
            "palpite_roubos": palpite_stl,
            "palpite_bloqueios": palpite_blk,
            "criado_em": pred.created_at,
        })

    return {
        "player_id": jogador_id,
        "nome_jogador": f"{jogador.firstname} {jogador.lastname}",
        "temporada": temporada_alvo,
        "total_predicoes": len(lista_resultado),
        "predicoes": lista_resultado,
    }
    
@router.post("/gerar/hoje")
def gerar_predicoes_hoje(temporada_alvo: int = Depends(obter_temporada), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    try:
        total = salvar_predicoes_dia_atual(db=db, season=temporada_alvo)
    except Exception as erro:
        logger.error(f"Falha ao gerar palpites do dia: {erro}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar palpites: {str(erro)}")

    return {
        "mensagem": "Palpites gerados com sucesso.",
        "temporada": temporada_alvo,
        "total_predicoes_geradas": total,
    }

@router.post("/gerar/temporada")
def gerar_predicoes_temporada(temporada: int = Query(...), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    try:
        total = salvar_predicoes_temporada(db=db, season=temporada)
    except Exception as erro:
        logger.error(f"Falha ao gerar palpites da temporada {temporada}: {erro}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar palpites: {str(erro)}")
 
    return {
        "mensagem": f"Palpites da temporada {temporada} geradas com sucesso.",
        "temporada": temporada,
        "total_predicoes_geradas": total,
    }

@router.post("/retroativo")
def gerar_predicoes_retroativo(db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    from app.services.manager_service import deletar_todas_predicoes, gerar_predicoes_retroativas
    from app.config import config

    season = config.NBA_SEASON
    try:
        deletar_todas_predicoes(db=db, season=season)
        total = gerar_predicoes_retroativas(db=db, season=season)
    except Exception as erro:
        logger.error(f"Falha ao gerar predicoes retroativas: {erro}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar predicoes retroativas: {str(erro)}")

    return {
        "mensagem": "Predicoes retroativas geradas com sucesso.",
        "temporada": season,
        "total": total,
    }