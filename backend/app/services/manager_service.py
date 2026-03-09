from datetime import datetime, timezone, timedelta
import logging

from app.db.models import Game, PlayerTeamSeason, Prediction
from app.services.prediction_service import prever_multiplas_stats_jogador

logger = logging.getLogger("manager_service")

def _buscar_jogos_do_dia(db, season):
    agora = datetime.now(timezone.utc)
    inicio_do_dia = agora.replace(hour=0, minute=0, second=0, microsecond=0)
    fim_do_dia = inicio_do_dia + timedelta(days=1)

    jogos = (db.query(Game).filter(Game.season == season, Game.date_start >= inicio_do_dia, Game.date_start < fim_do_dia).all())
    return jogos

def _buscar_jogadores_do_time(db, team_id, season):
    registros = (db.query(PlayerTeamSeason).filter(PlayerTeamSeason.team_id == team_id, PlayerTeamSeason.season == season, PlayerTeamSeason.active == True).all())

    lista_player_ids = []
    for registro in registros:
        lista_player_ids.append(registro.player_id)

    return lista_player_ids

def _predicao_ja_existe(db, player_id, game_id):
    existente = db.query(Prediction).filter(Prediction.player_id == player_id, Prediction.game_id == game_id).first()
    return existente is not None

def _gerar_predicao(db, player_id, game_id, team_id, opponent_team_id, is_home, season):
    previsoes = prever_multiplas_stats_jogador(db=db, player_id=player_id, opponent_team_id=opponent_team_id, season=season, is_home=is_home)

    predicted_points = previsoes.get("points", 0.0)
    predicted_assists = previsoes.get("assists", 0.0)
    predicted_rebounds = previsoes.get("rebounds", 0.0)
    predicted_steals = previsoes.get("steals", 0.0)
    predicted_blocks = previsoes.get("blocks", 0.0)

    nova_predicao = Prediction(
        player_id=player_id,
        game_id=game_id,
        team_id=team_id,
        opponent_team_id=opponent_team_id,
        season=season,
        is_home=is_home,
        predicted_points=predicted_points,
        predicted_assists=predicted_assists,
        predicted_rebounds=predicted_rebounds,
        predicted_steals=predicted_steals,
        predicted_blocks=predicted_blocks,
        created_at=datetime.now(timezone.utc)
    )

    db.add(nova_predicao)
    return nova_predicao

def salvar_predicoes_dia_atual(db, season):
    jogos_do_dia = _buscar_jogos_do_dia(db=db, season=season)

    if not jogos_do_dia:
        return 0

    total_geradas = 0
    total_erros = 0

    for jogo in jogos_do_dia:
        game_id = jogo.id
        home_team_id = jogo.home_team_id
        away_team_id = jogo.away_team_id

        jogadores_home = _buscar_jogadores_do_time(db=db, team_id=home_team_id, season=season)
        jogadores_away = _buscar_jogadores_do_time(db=db, team_id=away_team_id, season=season)

        for player_id in jogadores_home:
            if _predicao_ja_existe(db=db, player_id=player_id, game_id=game_id):
                continue

            try:
                _gerar_predicao(db=db, player_id=player_id, game_id=game_id, team_id=home_team_id, opponent_team_id=away_team_id, is_home=1, season=season)
                total_geradas += 1
            except Exception as e:
                total_erros += 1
                logger.error(f"Erro ao gerar previsão para jogador {player_id} no jogo {game_id}: {e}")
                continue

        for player_id in jogadores_away:
            if _predicao_ja_existe(db=db, player_id=player_id, game_id=game_id):
                continue

            try:
                _gerar_predicao(db=db, player_id=player_id, game_id=game_id, team_id=away_team_id, opponent_team_id=home_team_id, is_home=0, season=season)
                total_geradas += 1
            except Exception as e:
                total_erros += 1
                logger.error(f"Erro ao gerar previsão para jogador {player_id} no jogo {game_id}: {e}")
                continue
    db.commit()
    return total_geradas