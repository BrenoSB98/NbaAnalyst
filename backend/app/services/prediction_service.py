import logging
import numpy as np

from datetime import datetime, timezone
from sqlalchemy import func

from app.db.models import Game, PlayerGameStats, PlayerTeamSeason
from app.services import modelo_service

logger = logging.getLogger(__name__)

LIMIARES_MINIMOS = {}
LIMIARES_MINIMOS["points"] = 5.0
LIMIARES_MINIMOS["assists"] = 1.2
LIMIARES_MINIMOS["tot_reb"] = 2.5
LIMIARES_MINIMOS["steals"] = 0.5
LIMIARES_MINIMOS["blocks"] = 0.4

FATOR_POSICAO = {}
FATOR_POSICAO["PG"] = {"points": 1.0, "assists": 0.7, "steals": 0.7, "tot_reb": 1.3, "blocks": 1.5}
FATOR_POSICAO["SG"] = {"points": 1.0, "assists": 0.9, "steals": 0.8, "tot_reb": 1.2, "blocks": 1.4}
FATOR_POSICAO["SF"] = {"points": 1.0, "assists": 1.0, "steals": 1.0, "tot_reb": 0.9, "blocks": 1.1}
FATOR_POSICAO["PF"] = {"points": 1.0, "assists": 1.2, "steals": 1.1, "tot_reb": 0.8, "blocks": 0.8}
FATOR_POSICAO["C"] = {"points": 1.0, "assists": 1.3, "steals": 1.2, "tot_reb": 0.7, "blocks": 0.6}
FATOR_POSICAO["G"] = {"points": 1.0, "assists": 0.7, "steals": 0.7, "tot_reb": 1.3, "blocks": 1.5}
FATOR_POSICAO["F"] = {"points": 1.0, "assists": 1.0, "steals": 1.0, "tot_reb": 0.9, "blocks": 1.1}
FATOR_POSICAO["GF"] = {"points": 1.0, "assists": 0.8, "steals": 0.8, "tot_reb": 1.1, "blocks": 1.3}

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


def _traduzir_chave_stat(stat_name):
    if stat_name == "tot_reb":
        return "rebounds"
    return stat_name


def _obter_posicao_jogador(db, player_id, season):
    vinculo = db.query(PlayerTeamSeason).filter(PlayerTeamSeason.player_id == player_id, PlayerTeamSeason.season == season).first()
    if vinculo is None:
        return None
    if not vinculo.pos:
        return None
    pos_normalizada = vinculo.pos.split("-")[0]
    return pos_normalizada


def _calcular_medias_temporada_por_stat(db, player_id, season, data_corte=None):
    query = db.query(func.avg(PlayerGameStats.points).label("points"), func.avg(PlayerGameStats.assists).label("assists"), func.avg(PlayerGameStats.tot_reb).label("tot_reb"), func.avg(PlayerGameStats.steals).label("steals"), func.avg(PlayerGameStats.blocks).label("blocks")).join(Game, PlayerGameStats.game_id == Game.id).filter(PlayerGameStats.player_id == player_id, Game.season == season, Game.status_short == 3, Game.stage != 1)

    if data_corte is not None:
        query = query.filter(Game.date_start < data_corte)

    resultado = query.first()

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
        if media >= limiar_ajustado:
            stats_incluidas.append(stat_name)

    return stats_incluidas


def _carregar_historico_jogador(db, player_id, season, data_corte=None):
    query = db.query(PlayerGameStats, Game).join(Game, PlayerGameStats.game_id == Game.id).filter(PlayerGameStats.player_id == player_id, Game.season == season, Game.status_short == 3, Game.stage != 1)

    if data_corte is not None:
        query = query.filter(Game.date_start < data_corte)

    resultados = query.order_by(Game.date_start.asc()).all()
    return resultados


def _calcular_defesa_adversaria(db, opponent_team_id, season, stat_name, data_corte=None):
    query = db.query(PlayerGameStats).join(Game, PlayerGameStats.game_id == Game.id).filter(Game.season == season, Game.status_short == 3, Game.stage != 1, PlayerGameStats.team_id != opponent_team_id, (Game.home_team_id == opponent_team_id) | (Game.away_team_id == opponent_team_id))

    if data_corte is not None:
        query = query.filter(Game.date_start < data_corte)

    stats_sofridas = query.all()
    if not stats_sofridas:
        return 0.0

    total_stat = 0.0
    for s in stats_sofridas:
        total_stat = total_stat + float(getattr(s, stat_name, 0) or 0)

    query_jogos = db.query(Game).filter(Game.season == season, Game.status_short == 3, Game.stage != 1, (Game.home_team_id == opponent_team_id) | (Game.away_team_id == opponent_team_id))
    if data_corte is not None:
        query_jogos = query_jogos.filter(Game.date_start < data_corte)

    num_jogos = query_jogos.count()
    if num_jogos > 0:
        return round(total_stat / num_jogos, 2)
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


def extrair_features_avancadas_jogador(db, player_id, season, stat_name, data_corte=None):
    jogos_com_data = _carregar_historico_jogador(db, player_id, season, data_corte)

    if len(jogos_com_data) < 5:
        return None, None

    lista_features = []
    lista_alvos = []

    for idx in range(5, len(jogos_com_data)):
        stat_atual = jogos_com_data[idx][0]
        jogo_atual = jogos_com_data[idx][1]
        alvo = float(getattr(stat_atual, stat_name) or 0)

        inicio_10 = max(0, idx - 10)
        inicio_3 = max(0, idx - 3)

        valores_10 = []
        for j in jogos_com_data[inicio_10:idx]:
            valores_10.append(float(getattr(j[0], stat_name) or 0))

        valores_3 = []
        for j in jogos_com_data[inicio_3:idx]:
            valores_3.append(float(getattr(j[0], stat_name) or 0))

        valores_minutos = []
        for j in jogos_com_data[inicio_10:idx]:
            valores_minutos.append(converter_minutos_para_float(j[0].minutes))

        todos_anteriores = []
        for j in jogos_com_data[:idx]:
            todos_anteriores.append(float(getattr(j[0], stat_name) or 0))

        if todos_anteriores:
            media_temporada = float(np.mean(todos_anteriores))
        else:
            media_temporada = 0.0

        ema_ponderada = calcular_media_multi_janela(valores_3, valores_10, media_temporada)

        if valores_10:
            media_10 = float(np.mean(valores_10))
        else:
            media_10 = 0.0

        if valores_minutos:
            media_minutos = float(np.mean(valores_minutos))
        else:
            media_minutos = 0.0

        if len(valores_3) >= 2:
            eixo_x = np.arange(len(valores_3))
            inclinacao = float(np.polyfit(eixo_x, np.array(valores_3), 1)[0])
            variancia = float(np.std(valores_3))
        else:
            inclinacao = 0.0
            variancia = 0.0

        if stat_atual.team_id == jogo_atual.home_team_id:
            is_home = 1
        else:
            is_home = 0

        if idx >= 2:
            data_atual = jogos_com_data[idx][1].date_start
            data_anterior = jogos_com_data[idx - 1][1].date_start
            if data_atual is not None and data_anterior is not None:
                delta = (data_atual - data_anterior).days
                if delta == 1:
                    back_to_back = 1
                else:
                    back_to_back = 0
            else:
                back_to_back = 0
        else:
            back_to_back = 0

        vetor = [ema_ponderada, is_home, 0.0, 3, media_minutos, inclinacao, ema_ponderada, variancia, back_to_back, media_temporada, media_10]
        lista_features.append(vetor)
        lista_alvos.append(alvo)

    if len(lista_features) < 5:
        return None, None

    return lista_features, lista_alvos


def _montar_vetor_previsao(db, player_id, opponent_team_id, season, stat_name, em_casa, media_temporada, data_corte=None):
    limiar = LIMIARES_MINIMOS.get(stat_name, 0.0)
    if media_temporada < limiar:
        return None

    historico = _carregar_historico_jogador(db, player_id, season, data_corte)

    if not historico:
        return None

    historico_recente_10 = historico[-10:]
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

    ema_ponderada = calcular_media_multi_janela(valores_3, valores_10, media_temporada)

    if valores_10:
        media_10 = float(np.mean(valores_10))
    else:
        media_10 = media_temporada

    if valores_minutos:
        media_minutos = float(np.mean(valores_minutos))
    else:
        media_minutos = 0.0

    if len(valores_3) >= 2:
        eixo_x = np.arange(len(valores_3))
        inclinacao = float(np.polyfit(eixo_x, np.array(valores_3), 1)[0])
        variancia = float(np.std(valores_3))
    else:
        inclinacao = 0.0
        variancia = 0.0

    defesa_adversaria = _calcular_defesa_adversaria(db, opponent_team_id, season, stat_name, data_corte)

    media_vs_adversario = _calcular_media_vs_adversario(historico, opponent_team_id, stat_name)
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

    vetor = [ema_ponderada, em_casa, defesa_adversaria, dias_descanso, media_minutos, inclinacao, media_vs_adversario, variancia, back_to_back, media_temporada, media_10]
    return np.array([vetor])


def prever_performance_jogador_ml(db, player_id, opponent_team_id, season, stat_name, em_casa, media_temporada, data_corte=None):
    from xgboost import XGBRegressor

    modelo = modelo_service.carregar_modelo(player_id=player_id, stat_name=stat_name)

    if modelo is None:
        lista_features, lista_alvos = extrair_features_avancadas_jogador(db, player_id, season, stat_name, data_corte)
        if lista_features is None or len(lista_features) < 5:
            logger.debug(f"Dados insuficientes para previsão: player_id={player_id}, stat={stat_name}")
            return None

        modelo = XGBRegressor(n_estimators=150, max_depth=4, learning_rate=0.05, subsample=0.8, colsample_bytree=0.7, min_child_weight=5, gamma=0.1, reg_alpha=0.1, reg_lambda=2.0, random_state=42, objective="reg:squarederror", n_jobs=-1)
        modelo.fit(np.array(lista_features), np.array(lista_alvos))
        modelo_service.salvar_modelo(modelo, player_id, stat_name)

    vetor_previsao = _montar_vetor_previsao(db, player_id, opponent_team_id, season, stat_name, em_casa, media_temporada, data_corte)

    if vetor_previsao is None:
        logger.debug(f"Previsão ignorada (abaixo do limiar): player_id={player_id}, stat={stat_name}")
        return None

    resultado = modelo.predict(vetor_previsao)[0]
    return round(float(resultado), 2)


def prever_multiplas_stats_jogador(db, player_id, opponent_team_id, season, is_home, data_corte=None):
    pos_normalizada = _obter_posicao_jogador(db, player_id, season)
    medias_por_stat = _calcular_medias_temporada_por_stat(db, player_id, season, data_corte)
    stats_relevantes = _stats_relevantes_para_jogador(pos_normalizada, medias_por_stat)

    if not stats_relevantes:
        logger.debug(f"Nenhuma stat relevante: player_id={player_id}, pos={pos_normalizada}")

    previsoes = {}
    previsoes["points"] = None
    previsoes["assists"] = None
    previsoes["rebounds"] = None
    previsoes["steals"] = None
    previsoes["blocks"] = None

    for stat_name in stats_relevantes:
        media_temporada = medias_por_stat.get(stat_name, 0.0)
        previsao = prever_performance_jogador_ml(db=db, player_id=player_id, opponent_team_id=opponent_team_id, season=season, stat_name=stat_name, em_casa=is_home, media_temporada=media_temporada, data_corte=data_corte)
        if stat_name == "tot_reb":
            previsoes["rebounds"] = previsao
        else:
            previsoes[stat_name] = previsao

    return previsoes


def prever_performance_jogador(db, player_id, opponent_team_id, season, stat_name, em_casa):
    medias = _calcular_medias_temporada_por_stat(db, player_id, season)
    media_temporada = medias.get(stat_name, 0.0)
    return prever_performance_jogador_ml(db=db, player_id=player_id, opponent_team_id=opponent_team_id, season=season, stat_name=stat_name, em_casa=em_casa, media_temporada=media_temporada)