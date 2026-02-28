import os
import sys
import logging
from typing import Dict, Any

from sqlalchemy import func, inspect

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(BASE_DIR)
BACKEND_DIR = os.path.dirname(APP_DIR)

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from app.db.session import SessionLocal  # type: ignore
from app.db import models  # type: ignore

def obter_pk(modelo):
    map_col = inspect(modelo)
    pk_col = map_col.primary_key
    if pk_col:
        return pk_col[0]
    return None

def obter_contagem_tabelas():
    sessao = SessionLocal()
    try:
        contagens: Dict[str, int] = {}

        contagens["seasons"] = sessao.query(func.count("*")).select_from(models.Season).scalar() or 0
        contagens["leagues"] = sessao.query(func.count("*")).select_from(models.League).scalar() or 0
        contagens["teams"] = sessao.query(func.count("*")).select_from(models.Team).scalar() or 0
        contagens["players"] = sessao.query(func.count("*")).select_from(models.Player).scalar() or 0
        contagens["games"] = sessao.query(func.count("*")).select_from(models.Game).scalar() or 0
        contagens["game_team_scores"] = (sessao.query(func.count("*")).select_from(models.GameTeamScore).scalar() or 0)
        contagens["player_game_stats"] = (sessao.query(func.count("*")).select_from(models.PlayerGameStats).scalar() or 0)

        return contagens
    finally:
        sessao.close()

def verificar_db():
    sessao = SessionLocal()
    resultados: Dict[str, Any] = {}
    
    try:
        game_pk = obter_pk(models.Game)
        game_team_score_pk = obter_pk(models.GameTeamScore)
        player_pk = obter_pk(models.Player)
        player_game_stats_pk = obter_pk(models.PlayerGameStats)
        team_pk = obter_pk(models.Team)

        subquery_scores = (sessao.query(models.GameTeamScore.game_id).distinct())
        jogos_sem_scores = (sessao.query(game_pk).select_from(models.Game).filter(~game_pk.in_(subquery_scores)).count())
        resultados["jogos_sem_game_team_score"] = jogos_sem_scores
        
        subquery_games = sessao.query(game_pk).select_from(models.Game)
        scores_sem_game = (sessao.query(game_team_score_pk).select_from(models.GameTeamScore).filter(~models.GameTeamScore.game_id.in_(subquery_games)).count())
        resultados["game_team_scores_sem_game"] = scores_sem_game

        subquery_players = sessao.query(player_pk).select_from(models.Player)
        stats_sem_player = (sessao.query(player_game_stats_pk).select_from(models.PlayerGameStats).filter(~models.PlayerGameStats.player_id.in_(subquery_players)).count())
        resultados["player_game_stats_sem_player"] = stats_sem_player

        stats_sem_game = (sessao.query(player_game_stats_pk).select_from(models.PlayerGameStats).filter(~models.PlayerGameStats.game_id.in_(subquery_games)).count())
        resultados["player_game_stats_sem_game"] = stats_sem_game

        subquery_teams = sessao.query(team_pk).select_from(models.Team)
        stats_sem_team = (sessao.query(player_game_stats_pk).select_from(models.PlayerGameStats).filter(~models.PlayerGameStats.team_id.in_(subquery_teams)).count())
        resultados["player_game_stats_sem_team"] = stats_sem_team

        return resultados
    finally:
        sessao.close()

def reg_contagens(contagens):
    logger.info("=== Resumo de contagem por tabela ===")
    for nome_tabela, quantidade in contagens.items():
        logger.info("- %s: %d registros", nome_tabela, quantidade)

def reg_resumo(resultados):
    logger.info("=== Resumo de integridade básica ===")
    for chave, valor in resultados.items():
        logger.info("- %s: %s", chave, valor)

def executar_validacao():
    logger.info("Iniciando validação completa do banco de dados...")

    contagens = obter_contagem_tabelas()
    reg_contagens(contagens)

    resultados_integridade = verificar_db()
    reg_resumo(resultados_integridade)

    logger.info("Validação concluída.")

def listar_ids_jogos_sem_scores(limit):
    sessao = SessionLocal()
    try:
        game_pk = obter_pk(models.Game)
        
        subquery_scores = (sessao.query(models.GameTeamScore.game_id).distinct())
        jogos = (sessao.query(game_pk).select_from(models.Game).filter(~game_pk.in_(subquery_scores)).limit(limit).all())
        ids = [jogo[0] for jogo in jogos]
        return ids
    finally:
        sessao.close()

if __name__ == "__main__":
    """
    Exemplo de uso:
    docker compose exec backend python -m app.etl.validacao_db
    """
    executar_validacao()

    ids_sem_scores = listar_ids_jogos_sem_scores()
    if ids_sem_scores:
        logger.warning("Alguns jogos sem GameTeamScore: %s", ids_sem_scores)
    else:
        logger.info("Todos os jogos possuem GameTeamScore.")