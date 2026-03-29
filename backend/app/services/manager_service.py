from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import logging

from sqlalchemy.exc import IntegrityError

from app.config import config
from app.db.models import Game, PlayerGameStats, PlayerTeamSeason, Prediction
from app.services.prediction_service import prever_multiplas_stats_jogador

logger = logging.getLogger("manager_service")

FUSO_SP = ZoneInfo("America/Sao_Paulo")

def _converter_minutos(minutos_str):
    if not minutos_str:
        return 0.0

    minutos_limpo = str(minutos_str).strip()

    if minutos_limpo == "" or minutos_limpo == "0:00" or minutos_limpo == "00:00":
        return 0.0

    if ":" in minutos_limpo:
        partes = minutos_limpo.split(":")
        try:
            minutos = int(partes[0])
            segundos = int(partes[1])
            return minutos + (segundos / 60.0)
        except (ValueError, IndexError):
            return 0.0

    try:
        return float(minutos_limpo)
    except ValueError:
        return 0.0

def _buscar_jogadores_titulares(db, team_id, season):
    limiar = config.MIN_MINUTOS_PALPITE

    stats = db.query(PlayerGameStats).filter(PlayerGameStats.team_id == team_id, PlayerGameStats.season == season).all()

    soma_minutos = {}
    contagem_jogos = {}

    for stat in stats:
        pid = stat.player_id
        minutos = _converter_minutos(stat.minutes)

        if pid not in soma_minutos:
            soma_minutos[pid] = 0.0
            contagem_jogos[pid] = 0

        soma_minutos[pid] = soma_minutos[pid] + minutos
        contagem_jogos[pid] = contagem_jogos[pid] + 1

    lista_titulares = []
    for pid in soma_minutos:
        if contagem_jogos[pid] == 0:
            continue
        media = soma_minutos[pid] / contagem_jogos[pid]
        if media >= limiar:
            lista_titulares.append(pid)

    if not lista_titulares:
        logger.warning(f"Nenhum jogador acima do limiar de minutos")
        return _buscar_jogadores_do_time(db=db, team_id=team_id, season=season)

    lista_ativos = _filtrar_jogadores_ativos(db=db, player_ids=lista_titulares, team_id=team_id, season=season)
    if not lista_ativos:
        logger.warning(f"Nenhum jogador ativo nos ultimos jogos")
        return lista_titulares

    return lista_ativos

def _filtrar_jogadores_ativos(db, player_ids, team_id, season):
    ultimos_jogos = db.query(Game).filter(Game.season == season, Game.status_short == 3, (Game.home_team_id == team_id) | (Game.away_team_id == team_id)).order_by(Game.date_start.desc()).limit(5).all()

    if not ultimos_jogos:
        return player_ids

    ids_ultimos_jogos = []
    for jogo in ultimos_jogos:
        ids_ultimos_jogos.append(jogo.id)

    jogou_recentemente = set()
    for pid in player_ids:
        stats_recentes = db.query(PlayerGameStats).filter(PlayerGameStats.player_id == pid, PlayerGameStats.game_id.in_(ids_ultimos_jogos)).all()

        for stat in stats_recentes:
            minutos = _converter_minutos(stat.minutes)
            if minutos > 0:
                jogou_recentemente.add(pid)
                break

    lista_ativos = []
    for pid in player_ids:
        if pid in jogou_recentemente:
            lista_ativos.append(pid)

    return lista_ativos

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

def _processar_jogo(db, jogo, season, geradas, erros):
    game_id = jogo.id
    home_team_id = jogo.home_team_id
    away_team_id = jogo.away_team_id

    jogadores_casa = _buscar_jogadores_titulares(db=db, team_id=home_team_id, season=season)
    jogadores_fora = _buscar_jogadores_titulares(db=db, team_id=away_team_id, season=season)

    for player_id in jogadores_casa:
        if _predicao_ja_existe(db=db, player_id=player_id, game_id=game_id):
            continue

        try:
            with db.begin_nested():
                _gerar_predicao(db=db, player_id=player_id, game_id=game_id, team_id=home_team_id, opponent_team_id=away_team_id, is_home=1, season=season)
            geradas = geradas + 1
        except IntegrityError:
            logger.warning(f"Palpite ja existe (ignorado) —> player_id={player_id}, game_id={game_id}")
        except Exception as erro:
            erros = erros + 1
            logger.error(f"Erro ao gerar Palpite —> player_id={player_id}, game_id={game_id}: {erro}")

    for player_id in jogadores_fora:
        if _predicao_ja_existe(db=db, player_id=player_id, game_id=game_id):
            continue

        try:
            with db.begin_nested():
                _gerar_predicao(db=db, player_id=player_id, game_id=game_id, team_id=away_team_id, opponent_team_id=home_team_id, is_home=0, season=season)
            geradas = geradas + 1
        except IntegrityError:
            logger.warning(f"Palpite ja existe (ignorado) —> player_id={player_id}, game_id={game_id}")
        except Exception as erro:
            erros = erros + 1
            logger.error(f"Erro ao gerar palpite —> player_id={player_id}, game_id={game_id}: {erro}")

    return geradas, erros


def salvar_predicoes_dia_atual(db, season):
    jogos_do_dia = _buscar_jogos_do_dia(db=db, season=season)

    if not jogos_do_dia:
        logger.warning(f"Nenhum jogo encontrado para hoje —> temporada={season}")
        return 0

    geradas = 0
    erros = 0
    for jogo in jogos_do_dia:
        geradas, erros = _processar_jogo(db, jogo, season, geradas, erros)

    db.commit()
    logger.warning(f"Palpites do dia geradas —> total={geradas}, erros={erros}, temporada={season}")
    return geradas


def salvar_predicoes_temporada(db, season):
    jogos = db.query(Game).filter(Game.season == season, Game.status_short == 3).order_by(Game.date_start.asc()).all()

    if not jogos:
        logger.warning(f"Nenhum jogo finalizado encontrado —> temporada={season}")
        return 0

    geradas = 0
    erros = 0
    cont = 0
    for jogo in jogos:
        jogadores_casa = _buscar_jogadores_do_time(db=db, team_id=jogo.home_team_id, season=season)
        jogadores_fora = _buscar_jogadores_do_time(db=db, team_id=jogo.away_team_id, season=season)
        total_jogadores = len(jogadores_casa) + len(jogadores_fora)

        predicoes_existentes = db.query(Prediction).filter(Prediction.game_id == jogo.id).count()

        if total_jogadores > 0 and predicoes_existentes >= total_jogadores:
            continue

        geradas, erros = _processar_jogo(db, jogo, season, geradas, erros)
        cont = cont + 1

        if cont % 10 == 0:
            db.commit()
            logger.warning(f"Progresso —> jogos={cont}, predicoes={geradas}, erros={erros}, temporada={season}")

    db.commit()
    logger.warning(f"Palpites da temporada concluidas —> total={geradas}, erros={erros}, temporada={season}")
    return geradas