import logging
import os
import sys

from sqlalchemy import func, inspect

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(BASE_DIR)
BACKEND_DIR = os.path.dirname(APP_DIR)

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from app.db.session import SessionLocal
from app.db import models

logger = logging.getLogger(__name__)

def _obter_pk(modelo):
    mapa = inspect(modelo)
    pk_col = mapa.primary_key
    if pk_col:
        return pk_col[0]
    return None

def obter_contagem_tabelas():
    sessao = SessionLocal()
    try:
        contagens = {}
        contagens["seasons"] = sessao.query(func.count("*")).select_from(models.Season).scalar() or 0
        contagens["leagues"] = sessao.query(func.count("*")).select_from(models.League).scalar() or 0
        contagens["teams"] = sessao.query(func.count("*")).select_from(models.Team).scalar() or 0
        contagens["players"] = sessao.query(func.count("*")).select_from(models.Player).scalar() or 0
        contagens["games"] = sessao.query(func.count("*")).select_from(models.Game).scalar() or 0
        contagens["game_team_scores"] = sessao.query(func.count("*")).select_from(models.GameTeamScore).scalar() or 0
        contagens["player_game_stats"] = sessao.query(func.count("*")).select_from(models.PlayerGameStats).scalar() or 0
        return contagens
    finally:
        sessao.close()

def verificar_integridade_db():
    sessao = SessionLocal()
    resultados = {}

    try:
        game_pk = _obter_pk(models.Game)
        player_pk = _obter_pk(models.Player)
        player_game_stats_pk = _obter_pk(models.PlayerGameStats)
        game_team_score_pk = _obter_pk(models.GameTeamScore)
        team_pk = _obter_pk(models.Team)

        subquery_scores = sessao.query(models.GameTeamScore.game_id).distinct()
        resultados["jogos_sem_game_team_score"] = sessao.query(game_pk).select_from(models.Game).filter(~game_pk.in_(subquery_scores)).count()

        subquery_games = sessao.query(game_pk).select_from(models.Game)
        resultados["game_team_scores_sem_game"] = sessao.query(game_team_score_pk).select_from(models.GameTeamScore).filter(~models.GameTeamScore.game_id.in_(subquery_games)).count()

        subquery_players = sessao.query(player_pk).select_from(models.Player)
        resultados["player_game_stats_sem_player"] = sessao.query(player_game_stats_pk).select_from(models.PlayerGameStats).filter(~models.PlayerGameStats.player_id.in_(subquery_players)).count()
        resultados["player_game_stats_sem_game"] = sessao.query(player_game_stats_pk).select_from(models.PlayerGameStats).filter(~models.PlayerGameStats.game_id.in_(subquery_games)).count()

        subquery_teams = sessao.query(team_pk).select_from(models.Team)
        resultados["player_game_stats_sem_team"] = sessao.query(player_game_stats_pk).select_from(models.PlayerGameStats).filter(~models.PlayerGameStats.team_id.in_(subquery_teams)).count()

        return resultados
    finally:
        sessao.close()

def listar_ids_jogos_sem_scores(limit=20):
    sessao = SessionLocal()
    try:
        game_pk = _obter_pk(models.Game)
        subquery_scores = sessao.query(models.GameTeamScore.game_id).distinct()
        jogos = sessao.query(game_pk).select_from(models.Game).filter(~game_pk.in_(subquery_scores)).limit(limit).all()
        ids = [jogo[0] for jogo in jogos]
        return ids
    finally:
        sessao.close()

def executar_validacao():
    logger.warning("Iniciando validação do banco de dados...")
    contagens = obter_contagem_tabelas()
    for nome_tabela, quantidade in contagens.items():
        logger.warning("Contagem — %s: %d registros", nome_tabela, quantidade)

    resultados = verificar_integridade_db()
    problemas_encontrados = False
    for chave, valor in resultados.items():
        if valor > 0:
            problemas_encontrados = True
            logger.warning("Inconsistência detectada — %s: %d registros", chave, valor)

    if not problemas_encontrados:
        logger.warning("Integridade OK — nenhuma inconsistência encontrada.")

    ids_sem_scores = listar_ids_jogos_sem_scores()
    if ids_sem_scores:
        logger.warning("Jogos sem GameTeamScore (primeiros %d): %s", len(ids_sem_scores), ids_sem_scores)

    logger.warning("Validação concluída.")

if __name__ == "__main__":
    """
    Uso: docker compose exec backend python -m app.etl.validacao_db
    """
    executar_validacao()