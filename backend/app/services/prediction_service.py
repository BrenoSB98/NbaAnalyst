import logging
from datetime import datetime, timezone

import numpy as np
from sqlalchemy import func, select

from app.db.models import Game, GameTeamStats, PlayerGameStats, PlayerTeamSeason
from app.services import modelo_service

logger = logging.getLogger(__name__)

LIMIARES_MINIMOS = {}
LIMIARES_MINIMOS["points"] = 5.0
LIMIARES_MINIMOS["assists"] = 1.2
LIMIARES_MINIMOS["tot_reb"] = 2.5
LIMIARES_MINIMOS["steals"] = 0.5
LIMIARES_MINIMOS["blocks"] = 0.4

FATOR_POSICAO = {}
FATOR_POSICAO["PG"] = {
    "points": 1.0,
    "assists": 0.6,
    "steals": 0.7,
    "tot_reb": 1.4,
    "blocks": 2.0,
}
FATOR_POSICAO["SG"] = {
    "points": 1.0,
    "assists": 0.8,
    "steals": 0.8,
    "tot_reb": 1.3,
    "blocks": 1.8,
}
FATOR_POSICAO["SF"] = {
    "points": 1.0,
    "assists": 1.0,
    "steals": 0.9,
    "tot_reb": 1.0,
    "blocks": 1.2,
}
FATOR_POSICAO["PF"] = {
    "points": 1.0,
    "assists": 1.2,
    "steals": 1.0,
    "tot_reb": 0.7,
    "blocks": 0.8,
}
FATOR_POSICAO["C"] = {
    "points": 1.0,
    "assists": 1.4,
    "steals": 1.1,
    "tot_reb": 0.6,
    "blocks": 0.6,
}
FATOR_POSICAO["G"] = {
    "points": 1.0,
    "assists": 0.7,
    "steals": 0.7,
    "tot_reb": 1.4,
    "blocks": 2.0,
}
FATOR_POSICAO["F"] = {
    "points": 1.0,
    "assists": 1.1,
    "steals": 0.9,
    "tot_reb": 0.8,
    "blocks": 1.0,
}
FATOR_POSICAO["GF"] = {
    "points": 1.0,
    "assists": 0.9,
    "steals": 0.8,
    "tot_reb": 1.0,
    "blocks": 1.4,
}


def converter_minutos_para_float(minutos_str):
    if not minutos_str or minutos_str == "":
        return 0.0
    try:
        texto = str(minutos_str)
        if ":" in texto:
            partes = texto.split(":")
            return float(partes[0]) + (float(partes[1]) / 60)
        return float(texto)
    except (ValueError, AttributeError):
        return 0.0


def calcular_ema_ponderada(valores):
    if not valores:
        return 0.0
    soma_pesos = 0.0
    soma_ponderada = 0.0
    for i in range(len(valores)):
        peso = i + 1
        soma_ponderada = soma_ponderada + (valores[i] * peso)
        soma_pesos = soma_pesos + peso
    return round(soma_ponderada / soma_pesos, 4)


def calcular_media_multi_janela(valores_3, valores_10, media_temporada):
    ema_3 = calcular_ema_ponderada(valores_3)
    ema_10 = calcular_ema_ponderada(valores_10)
    resultado = (ema_3 * 0.40) + (ema_10 * 0.35) + (media_temporada * 0.25)
    return round(resultado, 4)


def _obter_posicao_jogador(db, player_id, season):
    stmt = (
        select(PlayerTeamSeason)
        .where(
            PlayerTeamSeason.player_id == player_id, PlayerTeamSeason.season == season
        )
        .order_by(PlayerTeamSeason.active.desc())
        .limit(1)
    )
    vinculo = db.execute(stmt).scalar_one_or_none()
    if vinculo is None:
        return None
    if not vinculo.pos:
        return None
    pos_normalizada = vinculo.pos.split("-")[0]
    return pos_normalizada


def _calcular_medias_temporada_por_stat(db, player_id, season, data_corte=None):
    stmt = (
        select(
            func.avg(PlayerGameStats.points).label("points"),
            func.avg(PlayerGameStats.assists).label("assists"),
            func.avg(PlayerGameStats.tot_reb).label("tot_reb"),
            func.avg(PlayerGameStats.steals).label("steals"),
            func.avg(PlayerGameStats.blocks).label("blocks"),
        )
        .join(Game, PlayerGameStats.game_id == Game.id)
        .where(
            PlayerGameStats.player_id == player_id,
            Game.season == season,
            Game.status_short == 3,
            Game.stage != 1,
        )
    )

    if data_corte is not None:
        stmt = stmt.where(Game.date_start < data_corte)

    resultado = db.execute(stmt).first()

    medias = {}
    if resultado:
        medias["points"] = round(float(resultado.points or 0), 2)
        medias["assists"] = round(float(resultado.assists or 0), 2)
        medias["tot_reb"] = round(float(resultado.tot_reb or 0), 2)
        medias["steals"] = round(float(resultado.steals or 0), 2)
        medias["blocks"] = round(float(resultado.blocks or 0), 2)
    else:
        medias["points"] = 0.0
        medias["assists"] = 0.0
        medias["tot_reb"] = 0.0
        medias["steals"] = 0.0
        medias["blocks"] = 0.0

    return medias


COBERTURA_ELITE = {}
COBERTURA_ELITE["points"] = 18.0
COBERTURA_ELITE["assists"] = 5.0
COBERTURA_ELITE["tot_reb"] = 8.0
COBERTURA_ELITE["steals"] = 1.3
COBERTURA_ELITE["blocks"] = 1.2


def _stats_relevantes_para_jogador(pos_normalizada, medias_por_stat):
    if pos_normalizada is not None:
        fatores = FATOR_POSICAO.get(pos_normalizada, {})
    else:
        fatores = {}

    stats_incluidas = []
    for stat_name in LIMIARES_MINIMOS:
        limiar_base = LIMIARES_MINIMOS[stat_name]
        fator = fatores.get(stat_name, 1.0)
        limiar_ajustado = limiar_base * fator
        media = medias_por_stat.get(stat_name, 0.0)
        limiar_elite = COBERTURA_ELITE.get(stat_name, 9999.0)
        if media >= limiar_ajustado:
            stats_incluidas.append(stat_name)
        elif media >= limiar_elite:
            stats_incluidas.append(stat_name)

    return stats_incluidas


def _carregar_historico_jogador(db, player_id, season, data_corte=None):
    stmt = (
        select(PlayerGameStats, Game)
        .join(Game, PlayerGameStats.game_id == Game.id)
        .where(
            PlayerGameStats.player_id == player_id,
            Game.season == season,
            Game.status_short == 3,
            Game.stage != 1,
        )
    )

    if data_corte is not None:
        stmt = stmt.where(Game.date_start < data_corte)

    stmt = stmt.order_by(Game.date_start.asc())
    resultados = db.execute(stmt).all()
    return resultados


def _calcular_usage_rate(historico_recente):
    soma_fga = 0.0
    soma_fta = 0.0
    soma_tov = 0.0
    soma_min = 0.0
    for stat, jogo in historico_recente:
        soma_fga = soma_fga + float(stat.fga or 0)
        soma_fta = soma_fta + float(stat.fta or 0)
        soma_tov = soma_tov + float(stat.turnovers or 0)
        soma_min = soma_min + converter_minutos_para_float(stat.minutes)
    posses = soma_fga + (0.44 * soma_fta) + soma_tov
    if soma_min > 0:
        return round(posses / soma_min, 3)
    return 0.0


def _calcular_defesa_adversaria_por_posicao(
    db, opponent_team_id, season, stat_name, pos_jogador, data_corte=None
):
    if pos_jogador is None:
        return _calcular_defesa_adversaria(
            db, opponent_team_id, season, stat_name, data_corte
        )

    stmt = (
        select(PlayerGameStats)
        .join(Game, PlayerGameStats.game_id == Game.id)
        .where(
            Game.season == season,
            Game.status_short == 3,
            Game.stage != 1,
            PlayerGameStats.team_id != opponent_team_id,
            (Game.home_team_id == opponent_team_id)
            | (Game.away_team_id == opponent_team_id),
        )
    )

    if data_corte is not None:
        stmt = stmt.where(Game.date_start < data_corte)

    stats_sofridas = db.execute(stmt).scalars().all()
    if not stats_sofridas:
        return _calcular_defesa_adversaria(
            db, opponent_team_id, season, stat_name, data_corte
        )

    total_stat = 0.0
    contagem = 0
    for s in stats_sofridas:
        if not s.pos:
            continue
        pos_s = s.pos.split("-")[0]
        if pos_s == pos_jogador:
            total_stat = total_stat + float(getattr(s, stat_name, 0) or 0)
            contagem = contagem + 1

    if contagem == 0:
        return _calcular_defesa_adversaria(
            db, opponent_team_id, season, stat_name, data_corte
        )

    return round(total_stat / contagem, 2)


def _calcular_defesa_adversaria(
    db, opponent_team_id, season, stat_name, data_corte=None
):
    stmt = (
        select(PlayerGameStats)
        .join(Game, PlayerGameStats.game_id == Game.id)
        .where(
            Game.season == season,
            Game.status_short == 3,
            Game.stage != 1,
            PlayerGameStats.team_id != opponent_team_id,
            (Game.home_team_id == opponent_team_id)
            | (Game.away_team_id == opponent_team_id),
        )
    )

    if data_corte is not None:
        stmt = stmt.where(Game.date_start < data_corte)

    stats_sofridas = db.execute(stmt).scalars().all()
    if not stats_sofridas:
        return 0.0

    total_stat = 0.0
    for s in stats_sofridas:
        total_stat = total_stat + float(getattr(s, stat_name, 0) or 0)

    stmt_jogos = select(func.count(Game.id)).where(
        Game.season == season,
        Game.status_short == 3,
        Game.stage != 1,
        (Game.home_team_id == opponent_team_id)
        | (Game.away_team_id == opponent_team_id),
    )
    if data_corte is not None:
        stmt_jogos = stmt_jogos.where(Game.date_start < data_corte)

    num_jogos = db.execute(stmt_jogos).scalar()
    if num_jogos > 0:
        return round(total_stat / num_jogos, 2)
    return 0.0


def _calcular_pace_adversario(db, opponent_team_id, season, data_corte=None):
    stmt = (
        select(GameTeamStats)
        .join(Game, GameTeamStats.game_id == Game.id)
        .where(
            Game.season == season,
            Game.status_short == 3,
            Game.stage != 1,
            GameTeamStats.team_id == opponent_team_id,
        )
    )
    if data_corte is not None:
        stmt = stmt.where(Game.date_start < data_corte)

    registros = db.execute(stmt).scalars().all()
    if not registros:
        return 0.0

    soma_pace = 0.0
    contagem = 0
    for r in registros:
        fga = float(r.fga or 0)
        fta = float(r.fta or 0)
        turnovers = float(r.turnovers or 0)
        pace = fga + (0.44 * fta) + turnovers
        soma_pace = soma_pace + pace
        contagem = contagem + 1

    if contagem > 0:
        return round(soma_pace / contagem, 2)
    return 0.0


def _calcular_media_vs_adversario(historico_jogador, opponent_team_id, stat_name):
    stats_vs = []
    for stat, jogo in historico_jogador:
        if jogo.home_team_id == stat.team_id:
            adversario_id = jogo.away_team_id
        else:
            adversario_id = jogo.home_team_id
        if adversario_id == opponent_team_id:
            v = float(getattr(stat, stat_name, 0) or 0)
            stats_vs.append(v)

    if not stats_vs:
        return None

    soma = 0.0
    for v in stats_vs:
        soma = soma + v
    return soma / len(stats_vs)


def _montar_vetor_previsao(
    db,
    player_id,
    opponent_team_id,
    season,
    stat_name,
    em_casa,
    media_temporada,
    pos_jogador=None,
    data_corte=None,
):
    limiar = LIMIARES_MINIMOS.get(stat_name, 0.0)
    if media_temporada < limiar:
        return None

    historico = _carregar_historico_jogador(db, player_id, season, data_corte)

    if not historico:
        return None

    historico_recente_10 = historico[-10:]
    historico_recente_5 = historico[-5:]
    historico_recente_3 = historico[-3:]

    valores_10 = []
    for stat, jogo in historico_recente_10:
        valores_10.append(float(getattr(stat, stat_name) or 0))

    valores_3 = []
    for stat, jogo in historico_recente_3:
        valores_3.append(float(getattr(stat, stat_name) or 0))

    valores_minutos = []
    for stat, jogo in historico_recente_10:
        valores_minutos.append(converter_minutos_para_float(stat.minutes))

    minutos_3 = []
    for stat, jogo in historico_recente_3:
        minutos_3.append(converter_minutos_para_float(stat.minutes))

    valores_fgp_5 = []
    for stat, jogo in historico_recente_5:
        valores_fgp_5.append(float(stat.fgp or 0))

    valores_ftp_5 = []
    for stat, jogo in historico_recente_5:
        valores_ftp_5.append(float(stat.ftp or 0))

    ema_ponderada = calcular_media_multi_janela(valores_3, valores_10, media_temporada)

    if valores_10:
        media_10 = float(np.mean(valores_10))
    else:
        media_10 = media_temporada

    if valores_minutos:
        media_minutos = float(np.mean(valores_minutos))
    else:
        media_minutos = 0.0

    if minutos_3:
        media_minutos_3 = float(np.mean(minutos_3))
    else:
        media_minutos_3 = 0.0

    if valores_fgp_5:
        fgp_media_5 = float(np.mean(valores_fgp_5))
    else:
        fgp_media_5 = 0.0

    if valores_ftp_5:
        ftp_media_5 = float(np.mean(valores_ftp_5))
    else:
        ftp_media_5 = 0.0

    if len(valores_3) >= 2:
        eixo_x = np.arange(len(valores_3))
        inclinacao = float(np.polyfit(eixo_x, np.array(valores_3), 1)[0])
        variancia = float(np.std(valores_3))
    else:
        inclinacao = 0.0
        variancia = 0.0

    defesa_adversaria_geral = _calcular_defesa_adversaria(
        db, opponent_team_id, season, stat_name, data_corte
    )
    pace_adversario = _calcular_pace_adversario(
        db, opponent_team_id, season, data_corte
    )
    usage_rate = _calcular_usage_rate(historico_recente_10)

    media_vs_adversario = _calcular_media_vs_adversario(
        historico, opponent_team_id, stat_name
    )
    if media_vs_adversario is None:
        media_vs_adversario = ema_ponderada

    if data_corte is not None:
        agora = data_corte
    else:
        agora = datetime.now(timezone.utc)

    if historico:
        data_ultimo = historico[-1][1].date_start
        if data_ultimo is not None:
            if data_ultimo.tzinfo is None:
                data_ultimo = data_ultimo.replace(tzinfo=timezone.utc)
            if agora.tzinfo is None:
                agora = agora.replace(tzinfo=timezone.utc)
            dias_descanso = min((agora - data_ultimo).days, 7)
        else:
            dias_descanso = 3
    else:
        dias_descanso = 3

    if dias_descanso <= 1:
        back_to_back = 1
    else:
        back_to_back = 0

    if media_minutos > 0:
        taxa_participacao = media_minutos_3 / media_minutos
    else:
        taxa_participacao = 1.0

    vetor = [
        ema_ponderada,
        media_temporada,
        media_minutos,
        defesa_adversaria_geral,
        inclinacao,
        variancia,
        pace_adversario,
        fgp_media_5,
        usage_rate,
    ]
    return np.array([vetor])


def prever_performance_jogador_ml(
    db,
    player_id,
    opponent_team_id,
    season,
    stat_name,
    em_casa,
    media_temporada,
    pos_jogador=None,
    data_corte=None,
):
    modelo = modelo_service.carregar_modelo(player_id=player_id, stat_name=stat_name)

    if modelo is None:
        logger.debug(f"Modelo ausente: player_id={player_id}, stat={stat_name}")
        return None

    vetor_previsao = _montar_vetor_previsao(
        db,
        player_id,
        opponent_team_id,
        season,
        stat_name,
        em_casa,
        media_temporada,
        pos_jogador,
        data_corte,
    )

    if vetor_previsao is None:
        logger.debug(
            f"Previsao ignorada (abaixo do limiar): player_id={player_id}, stat={stat_name}"
        )
        return None

    resultado = modelo.predict(vetor_previsao)[0]
    valor_final = round(float(resultado), 2)
    logger.debug(
        f"Previsao gerada: player_id={player_id}, stat={stat_name}, valor={valor_final}"
    )
    return valor_final


def _calcular_coef_variacao(db, player_id, season, stat_name, data_corte=None):
    historico = _carregar_historico_jogador(db, player_id, season, data_corte)
    if not historico:
        return None
    valores = []
    for stat, jogo in historico[-15:]:
        valores.append(float(getattr(stat, stat_name, 0) or 0))
    if len(valores) < 3:
        return None
    media = float(np.mean(valores))
    if media <= 0:
        return None
    desvio = float(np.std(valores))
    return desvio / media


def _calcular_media_recente(db, player_id, season, stat_name, data_corte=None):
    historico = _carregar_historico_jogador(db, player_id, season, data_corte)
    if not historico:
        return None
    valores = []
    for stat, jogo in historico[-15:]:
        valores.append(float(getattr(stat, stat_name, 0) or 0))
    if len(valores) == 0:
        return None
    return float(np.mean(valores))


def prever_multiplas_stats_jogador(
    db, player_id, opponent_team_id, season, is_home, data_corte=None
):
    from app.services.formatar_palpites import calcular_linha_referencia

    pos_normalizada = _obter_posicao_jogador(db, player_id, season)
    medias_por_stat = _calcular_medias_temporada_por_stat(
        db, player_id, season, data_corte
    )
    stats_relevantes = _stats_relevantes_para_jogador(pos_normalizada, medias_por_stat)

    if not stats_relevantes:
        logger.debug(
            f"Nenhuma stat relevante: player_id={player_id}, pos={pos_normalizada}"
        )

    previsoes = {}
    previsoes["points"] = None
    previsoes["assists"] = None
    previsoes["rebounds"] = None
    previsoes["steals"] = None
    previsoes["blocks"] = None

    for stat_name in stats_relevantes:
        media_temporada = medias_por_stat.get(stat_name, 0.0)
        previsao = prever_performance_jogador_ml(
            db=db,
            player_id=player_id,
            opponent_team_id=opponent_team_id,
            season=season,
            stat_name=stat_name,
            em_casa=is_home,
            media_temporada=media_temporada,
            pos_jogador=pos_normalizada,
            data_corte=data_corte,
        )
        if previsao is None:
            continue
        media_recente = _calcular_media_recente(
            db, player_id, season, stat_name, data_corte
        )
        linha = calcular_linha_referencia(media_recente)
        if linha is None:
            continue
        coef = _calcular_coef_variacao(db, player_id, season, stat_name, data_corte)
        item = {}
        item["valor"] = previsao
        item["linha"] = linha
        item["coef_variacao"] = coef
        if stat_name == "tot_reb":
            previsoes["rebounds"] = item
        else:
            previsoes[stat_name] = item

    return previsoes


def prever_performance_jogador(
    db, player_id, opponent_team_id, season, stat_name, em_casa
):
    medias = _calcular_medias_temporada_por_stat(db, player_id, season)
    media_temporada = medias.get(stat_name, 0.0)
    return prever_performance_jogador_ml(
        db=db,
        player_id=player_id,
        opponent_team_id=opponent_team_id,
        season=season,
        stat_name=stat_name,
        em_casa=em_casa,
        media_temporada=media_temporada,
    )
