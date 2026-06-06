import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import delete, func, select
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


def _buscar_jogadores_titulares(db, team_id, season, data_corte=None):
    limiar = config.MIN_MINUTOS_PALPITE
    janela = config.JANELA_JOGOS_RECENTES
    stmt = (
        select(PlayerGameStats, Game)
        .join(Game, PlayerGameStats.game_id == Game.id)
        .where(
            PlayerGameStats.team_id == team_id,
            PlayerGameStats.season == season,
            Game.status_short == 3,
        )
    )
    if data_corte is not None:
        stmt = stmt.where(Game.date_start < data_corte)
    stmt = stmt.order_by(Game.date_start.desc())
    resultados = db.execute(stmt).all()

    jogos_por_jogador = {}
    for stat, jogo in resultados:
        pid = stat.player_id
        if pid not in jogos_por_jogador:
            jogos_por_jogador[pid] = []
        if len(jogos_por_jogador[pid]) < janela:
            jogos_por_jogador[pid].append(_converter_minutos(stat.minutes))

    lista_titulares = []
    for pid in jogos_por_jogador:
        jogos = jogos_por_jogador[pid]
        if len(jogos) == 0:
            continue
        soma = 0.0
        for m in jogos:
            soma = soma + m
        media = soma / len(jogos)
        if media >= limiar:
            lista_titulares.append(pid)

    if not lista_titulares:
        return _buscar_jogadores_do_time(db=db, team_id=team_id, season=season)

    if data_corte is None:
        lista_ativos = _filtrar_jogadores_ativos(
            db=db, player_ids=lista_titulares, team_id=team_id, season=season
        )
        if not lista_ativos:
            return lista_titulares
        return lista_ativos

    return lista_titulares


def _filtrar_jogadores_ativos(db, player_ids, team_id, season):
    qtd_jogos = config.JOGOS_CHECAGEM_ATIVIDADE
    limiar_minutos_recente = config.MIN_MINUTOS_JOGO_RECENTE
    stmt = (
        select(Game)
        .where(
            Game.season == season,
            Game.status_short == 3,
            (Game.home_team_id == team_id) | (Game.away_team_id == team_id),
        )
        .order_by(Game.date_start.desc())
        .limit(qtd_jogos)
    )
    ultimos_jogos = db.execute(stmt).scalars().all()

    if not ultimos_jogos:
        return player_ids

    ids_ultimos_jogos = []
    for jogo in ultimos_jogos:
        ids_ultimos_jogos.append(jogo.id)

    jogou_recentemente = set()
    for pid in player_ids:
        stmt_stats = select(PlayerGameStats).where(
            PlayerGameStats.player_id == pid,
            PlayerGameStats.game_id.in_(ids_ultimos_jogos),
        )
        stats_recentes = db.execute(stmt_stats).scalars().all()
        for stat in stats_recentes:
            minutos = _converter_minutos(stat.minutes)
            if minutos >= limiar_minutos_recente:
                jogou_recentemente.add(pid)
                break

    lista_ativos = []
    for pid in player_ids:
        if pid in jogou_recentemente:
            lista_ativos.append(pid)

    return lista_ativos


def _buscar_jogos_do_dia(db, season):
    agora_sp = datetime.now(FUSO_SP)
    agora_utc = agora_sp.astimezone(timezone.utc)
    inicio_sp = agora_sp.replace(hour=0, minute=0, second=0, microsecond=0)
    fim_sp = inicio_sp + timedelta(days=1)
    inicio_utc = inicio_sp.astimezone(timezone.utc)
    fim_utc = fim_sp.astimezone(timezone.utc)
    stmt = select(Game).where(
        Game.season == season,
        Game.status_short == 1,
        Game.stage != 1,
        Game.date_start >= inicio_utc,
        Game.date_start < fim_utc,
        Game.date_start > agora_utc,
    )
    jogos = db.execute(stmt).scalars().all()
    logger.info(
        f"Jogos agendados encontrados para hoje: total={len(jogos)}, temporada={season}, agora_sp={agora_sp.strftime('%H:%M')}"
    )
    return jogos


def _buscar_jogadores_do_time(db, team_id, season):
    stmt = select(PlayerTeamSeason).where(
        PlayerTeamSeason.team_id == team_id,
        PlayerTeamSeason.season == season,
        PlayerTeamSeason.active,
    )
    registros = db.execute(stmt).scalars().all()
    if not registros:
        stmt = select(PlayerTeamSeason).where(
            PlayerTeamSeason.team_id == team_id, PlayerTeamSeason.season == season
        )
        registros = db.execute(stmt).scalars().all()
    lista_ids = []
    for registro in registros:
        lista_ids.append(registro.player_id)
    return lista_ids


def _predicao_ja_existe(db, player_id, game_id):
    stmt = select(Prediction).where(
        Prediction.player_id == player_id, Prediction.game_id == game_id
    )
    existente = db.execute(stmt).first()
    if existente:
        return True
    return False


def _aplicar_filtro_confianca(item_previsao):
    if item_previsao is None:
        return None, None
    coef_maximo = config.COEF_VARIACAO_MAXIMO
    valor = item_previsao.get("valor", None)
    linha = item_previsao.get("linha", None)
    coef = item_previsao.get("coef_variacao", None)
    if valor is None:
        return None, None
    if coef is None:
        return valor, linha
    if coef > coef_maximo:
        return None, None
    return valor, linha


def _gerar_predicao(
    db, player_id, game_id, team_id, opponent_team_id, is_home, season, data_corte=None
):
    previsoes = prever_multiplas_stats_jogador(
        db=db,
        player_id=player_id,
        opponent_team_id=opponent_team_id,
        season=season,
        is_home=is_home,
        data_corte=data_corte,
    )

    pontos_previstos, linha_pontos = _aplicar_filtro_confianca(
        previsoes.get("points", None)
    )
    assist_previstos, linha_assist = _aplicar_filtro_confianca(
        previsoes.get("assists", None)
    )
    rebotes_previstos, linha_rebotes = _aplicar_filtro_confianca(
        previsoes.get("rebounds", None)
    )
    roubos_previstos, linha_roubos = _aplicar_filtro_confianca(
        previsoes.get("steals", None)
    )
    bloqueios_previstos, linha_bloqueios = _aplicar_filtro_confianca(
        previsoes.get("blocks", None)
    )

    if (
        pontos_previstos is None
        and assist_previstos is None
        and rebotes_previstos is None
        and roubos_previstos is None
        and bloqueios_previstos is None
    ):
        logger.debug(
            f"Nenhuma previsao confiavel: player_id={player_id}, game_id={game_id}"
        )
        return None

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
        linha_points=linha_pontos,
        linha_assists=linha_assist,
        linha_rebounds=linha_rebotes,
        linha_steals=linha_roubos,
        linha_blocks=linha_bloqueios,
        created_at=datetime.now(timezone.utc),
    )

    db.add(nova_predicao)
    return nova_predicao


def _processar_jogo(db, jogo, season, total_geradas, total_erros, data_corte=None):
    game_id = jogo.id
    home_team_id = jogo.home_team_id
    away_team_id = jogo.away_team_id

    jogadores_casa = _buscar_jogadores_titulares(
        db=db, team_id=home_team_id, season=season, data_corte=data_corte
    )
    jogadores_fora = _buscar_jogadores_titulares(
        db=db, team_id=away_team_id, season=season, data_corte=data_corte
    )

    for player_id in jogadores_casa:
        if _predicao_ja_existe(db=db, player_id=player_id, game_id=game_id):
            continue
        try:
            with db.begin_nested():
                predicao = _gerar_predicao(
                    db=db,
                    player_id=player_id,
                    game_id=game_id,
                    team_id=home_team_id,
                    opponent_team_id=away_team_id,
                    is_home=1,
                    season=season,
                    data_corte=data_corte,
                )
            if predicao is not None:
                total_geradas = total_geradas + 1
        except IntegrityError:
            logger.warning(
                f"Predicao ja existe (ignorado): player_id={player_id}, game_id={game_id}"
            )
        except Exception as erro:
            total_erros = total_erros + 1
            logger.error(
                f"Erro ao gerar predicao: player_id={player_id}, game_id={game_id}: {erro}"
            )

    for player_id in jogadores_fora:
        if _predicao_ja_existe(db=db, player_id=player_id, game_id=game_id):
            continue
        try:
            with db.begin_nested():
                predicao = _gerar_predicao(
                    db=db,
                    player_id=player_id,
                    game_id=game_id,
                    team_id=away_team_id,
                    opponent_team_id=home_team_id,
                    is_home=0,
                    season=season,
                    data_corte=data_corte,
                )
            if predicao is not None:
                total_geradas = total_geradas + 1
        except IntegrityError:
            logger.warning(
                f"Predicao ja existe (ignorado): player_id={player_id}, game_id={game_id}"
            )
        except Exception as erro:
            total_erros = total_erros + 1
            logger.error(
                f"Erro ao gerar predicao: player_id={player_id}, game_id={game_id}: {erro}"
            )

    return total_geradas, total_erros


def salvar_predicoes_dia_atual(db, season):
    jogos_do_dia = _buscar_jogos_do_dia(db=db, season=season)

    if not jogos_do_dia:
        logger.info(f"Nenhum jogo encontrado para hoje: temporada={season}")
        return 0

    total_geradas = 0
    total_erros = 0

    for jogo in jogos_do_dia:
        total_geradas, total_erros = _processar_jogo(
            db, jogo, season, total_geradas, total_erros
        )

    db.commit()
    logger.info(
        f"Predicoes do dia geradas: total={total_geradas}, erros={total_erros}, temporada={season}"
    )
    return total_geradas


def deletar_todas_predicoes(db, season):
    stmt = delete(Prediction).where(Prediction.season == season)
    resultado = db.execute(stmt)
    total = resultado.rowcount
    db.commit()
    logger.info(f"Predicoes deletadas: total={total}, temporada={season}")
    return total


def gerar_predicoes_retroativas(db, season):
    stmt = (
        select(Game)
        .where(Game.season == season, Game.status_short == 3, Game.stage != 1)
        .order_by(Game.date_start.asc())
    )
    jogos = db.execute(stmt).scalars().all()

    if not jogos:
        logger.warning(f"Nenhum jogo finalizado encontrado: temporada={season}")
        return 0

    total_geradas = 0
    total_erros = 0
    contador = 0

    for jogo in jogos:
        data_corte = jogo.date_start
        count_stmt = select(func.count(Prediction.id)).where(
            Prediction.game_id == jogo.id
        )
        predicoes_existentes = db.execute(count_stmt).scalar()
        if predicoes_existentes > 0:
            continue

        total_geradas, total_erros = _processar_jogo(
            db, jogo, season, total_geradas, total_erros, data_corte=data_corte
        )
        contador = contador + 1

        if contador % 10 == 0:
            db.commit()
            logger.info(
                f"Progresso retroativo: jogos={contador}, predicoes={total_geradas}, erros={total_erros}, temporada={season}"
            )

    db.commit()
    logger.info(
        f"Predicoes retroativas concluidas: total={total_geradas}, erros={total_erros}, temporada={season}"
    )
    return total_geradas


def salvar_predicoes_temporada(db, season):
    stmt = (
        select(Game)
        .where(Game.season == season, Game.status_short == 3, Game.stage != 1)
        .order_by(Game.date_start.asc())
    )
    jogos = db.execute(stmt).scalars().all()

    if not jogos:
        logger.warning(f"Nenhum jogo finalizado encontrado: temporada={season}")
        return 0

    total_geradas = 0
    total_erros = 0
    contador = 0

    for jogo in jogos:
        jogadores_casa = _buscar_jogadores_do_time(
            db=db, team_id=jogo.home_team_id, season=season
        )
        jogadores_fora = _buscar_jogadores_do_time(
            db=db, team_id=jogo.away_team_id, season=season
        )
        total_jogadores = len(jogadores_casa) + len(jogadores_fora)
        count_stmt = select(func.count(Prediction.id)).where(
            Prediction.game_id == jogo.id
        )
        predicoes_existentes = db.execute(count_stmt).scalar()

        if total_jogadores > 0 and predicoes_existentes >= total_jogadores:
            continue

        total_geradas, total_erros = _processar_jogo(
            db, jogo, season, total_geradas, total_erros
        )
        contador = contador + 1

        if contador % 10 == 0:
            db.commit()
            logger.info(
                f"Progresso: jogos={contador}, predicoes={total_geradas}, erros={total_erros}, temporada={season}"
            )

    db.commit()
    logger.info(
        f"Predicoes da temporada concluidas: total={total_geradas}, erros={total_erros}, temporada={season}"
    )
    return total_geradas
