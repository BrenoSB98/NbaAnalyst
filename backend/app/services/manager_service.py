from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import logging

from sqlalchemy.exc import IntegrityError

from app.db.models import Game, PlayerTeamSeason, Prediction
from app.services.prediction_service import prever_multiplas_stats_jogador

logger = logging.getLogger("manager_service")

FUSO_SP = ZoneInfo("America/Sao_Paulo")

def _buscar_jogos_do_dia(db, season):
    agora_sp = datetime.now(FUSO_SP)
    inicio_sp = agora_sp.replace(hour=0, minute=0, second=0, microsecond=0)
    fim_sp = inicio_sp + timedelta(days=1, hours=6)
    inicio_utc = inicio_sp.astimezone(timezone.utc)
    fim_utc = fim_sp.astimezone(timezone.utc)

    jogos = db.query(Game).filter(Game.season == season, Game.date_start >= inicio_utc, Game.date_start < fim_utc).all()
    return jogos

def _buscar_jogadores_do_time(db, team_id, season):
    registros = db.query(PlayerTeamSeason).filter(PlayerTeamSeason.team_id == team_id, PlayerTeamSeason.season == season, PlayerTeamSeason.active == True).all()

    if not registros:
        registros = db.query(PlayerTeamSeason).filter(PlayerTeamSeason.team_id == team_id, PlayerTeamSeason.season == season).all()

    lista_ids = []
    for registro in registros:
        lista_ids.append(registro.player_id)

    return lista_ids

def _predicao_ja_existe(db, player_id, game_id):
    existente = db.query(Prediction).filter(Prediction.player_id == player_id, Prediction.game_id == game_id).first()

    if existente:
        return True
    else:
        return False

def _gerar_predicao(db, player_id, game_id, team_id, opponent_team_id, is_home, season):
    previsoes = prever_multiplas_stats_jogador(db=db, player_id=player_id, opponent_team_id=opponent_team_id, season=season, is_home=is_home)

    pontos_previstos = previsoes.get("points", 0.0)
    assist_previstos = previsoes.get("assists", 0.0)
    rebotes_previstos = previsoes.get("rebounds", 0.0)
    roubos_previstos = previsoes.get("steals", 0.0)
    bloqueios_previstos = previsoes.get("blocks", 0.0)

    nova_predicao = Prediction(
        player_id=player_id,
        game_id=game_id,
        team_id=team_id,
        opponent_team_id=opponent_team_id,
        season=season,
        is_home=is_home,
        predicted_points=pontos_previstos,
        predicted_assists=assist_previstos,
        predicted_rebounds=rebotes_previstos,
        predicted_steals=roubos_previstos,
        predicted_blocks=bloqueios_previstos,
        created_at=datetime.now(timezone.utc),
    )

    db.add(nova_predicao)
    return nova_predicao

def _processar_jogo(db, jogo, season, total_geradas, total_erros):
    game_id = jogo.id
    home_team_id = jogo.home_team_id
    away_team_id = jogo.away_team_id

    jogadores_casa = _buscar_jogadores_do_time(db=db, team_id=home_team_id, season=season)
    jogadores_fora = _buscar_jogadores_do_time(db=db, team_id=away_team_id, season=season)

    for player_id in jogadores_casa:
        if _predicao_ja_existe(db=db, player_id=player_id, game_id=game_id):
            continue

        try:
            with db.begin_nested():
                _gerar_predicao(db=db, player_id=player_id, game_id=game_id, team_id=home_team_id, opponent_team_id=away_team_id, is_home=1, season=season)
            total_geradas = total_geradas + 1
        except IntegrityError:
            logger.warning(f"Predicao ja existe (ignorado) —> player_id={player_id}, game_id={game_id}")
        except Exception as erro:
            total_erros = total_erros + 1
            logger.error(f"Erro ao gerar predicao —> player_id={player_id}, game_id={game_id}: {erro}")

    for player_id in jogadores_fora:
        if _predicao_ja_existe(db=db, player_id=player_id, game_id=game_id):
            continue

        try:
            with db.begin_nested():
                _gerar_predicao(db=db, player_id=player_id, game_id=game_id, team_id=away_team_id, opponent_team_id=home_team_id, is_home=0, season=season)
            total_geradas = total_geradas + 1
        except IntegrityError:
            logger.warning(f"Predicao ja existe (ignorado) —> player_id={player_id}, game_id={game_id}")
        except Exception as erro:
            total_erros = total_erros + 1
            logger.error(f"Erro ao gerar predicao —> player_id={player_id}, game_id={game_id}: {erro}")

    return total_geradas, total_erros


def salvar_predicoes_dia_atual(db, season):
    jogos_do_dia = _buscar_jogos_do_dia(db=db, season=season)

    if not jogos_do_dia:
        logger.warning(f"Nenhum jogo encontrado para hoje —> temporada={season}")
        return 0

    total_geradas = 0
    total_erros = 0

    for jogo in jogos_do_dia:
        total_geradas, total_erros = _processar_jogo(db, jogo, season, total_geradas, total_erros)

    db.commit()
    logger.warning(f"Predicoes do dia geradas —> total={total_geradas}, erros={total_erros}, temporada={season}")
    return total_geradas


def salvar_predicoes_temporada(db, season):
    jogos = db.query(Game).filter(Game.season == season, Game.status_short == 3).order_by(Game.date_start.asc()).all()

    if not jogos:
        logger.warning(f"Nenhum jogo finalizado encontrado —> temporada={season}")
        return 0

    total_geradas = 0
    total_erros = 0
    contador = 0

    for jogo in jogos:
        jogadores_casa = _buscar_jogadores_do_time(db=db, team_id=jogo.home_team_id, season=season)
        jogadores_fora = _buscar_jogadores_do_time(db=db, team_id=jogo.away_team_id, season=season)
        total_jogadores = len(jogadores_casa) + len(jogadores_fora)

        predicoes_existentes = db.query(Prediction).filter(Prediction.game_id == jogo.id).count()

        if total_jogadores > 0 and predicoes_existentes >= total_jogadores:
            continue

        total_geradas, total_erros = _processar_jogo(db, jogo, season, total_geradas, total_erros)
        contador = contador + 1

        if contador % 10 == 0:
            db.commit()
            logger.warning(f"Progresso —> jogos={contador}, predicoes={total_geradas}, erros={total_erros}, temporada={season}")

    db.commit()
    logger.warning(f"Predicoes da temporada concluidas —> total={total_geradas}, erros={total_erros}, temporada={season}")
    return total_geradas