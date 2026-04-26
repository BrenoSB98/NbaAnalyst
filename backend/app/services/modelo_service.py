import os
import logging
import numpy as np

from app.config import config
from app.db.models import Game, PlayerGameStats

logger = logging.getLogger(__name__)

STATS_PARA_TREINAR = ["points", "assists", "tot_reb", "steals", "blocks"]
N_ESTIMADORES_TOTAL = 150

LIMIARES_TREINO = {}
LIMIARES_TREINO["points"] = 5.0
LIMIARES_TREINO["assists"] = 1.2
LIMIARES_TREINO["tot_reb"] = 2.5
LIMIARES_TREINO["steals"] = 0.5
LIMIARES_TREINO["blocks"] = 0.4


def _converter_minutos(minutos_str):
    if not minutos_str:
        return 0.0
    minutos_limpo = str(minutos_str).strip()
    if minutos_limpo == "" or minutos_limpo == "0:00" or minutos_limpo == "00:00":
        return 0.0
    if ":" in minutos_limpo:
        partes = minutos_limpo.split(":")
        try:
            return int(partes[0]) + (int(partes[1]) / 60.0)
        except (ValueError, IndexError):
            return 0.0
    try:
        return float(minutos_limpo)
    except ValueError:
        return 0.0


def _caminho_modelo(player_id, stat_name):
    pasta = config.PASTA_MODELOS
    return os.path.join(pasta, f"modelo_{player_id}_{stat_name}.pkl")


def salvar_modelo(modelo, player_id, stat_name):
    import pickle
    pasta = config.PASTA_MODELOS
    if not os.path.exists(pasta):
        os.makedirs(pasta)
    caminho = _caminho_modelo(player_id, stat_name)
    with open(caminho, "wb") as arquivo:
        pickle.dump(modelo, arquivo)


def carregar_modelo(player_id, stat_name):
    import pickle
    caminho = _caminho_modelo(player_id, stat_name)
    if not os.path.exists(caminho):
        return None
    try:
        with open(caminho, "rb") as arquivo:
            return pickle.load(arquivo)
    except Exception as erro:
        logger.warning(f"Falha ao carregar modelo: player_id={player_id}, stat={stat_name}: {erro}")
        return None


def _treinar_modelo_novo(lista_features, lista_alvos):
    from xgboost import XGBRegressor
    matriz = np.array(lista_features)
    alvos = np.array(lista_alvos)
    modelo = XGBRegressor(n_estimators=N_ESTIMADORES_TOTAL, max_depth=4, learning_rate=0.05, subsample=0.8, colsample_bytree=0.7, min_child_weight=5, gamma=0.1, reg_alpha=0.1, reg_lambda=2.0, random_state=42, objective="reg:squarederror", n_jobs=-1)
    modelo.fit(matriz, alvos)
    return modelo


def _treinar_modelo_jogador(player_id, stat_name, lista_features, lista_alvos):
    if lista_features is None or len(lista_features) < 5:
        return None
    logger.info(f"Treinando: player_id={player_id}, stat={stat_name}, amostras={len(lista_features)}")
    return _treinar_modelo_novo(lista_features, lista_alvos)


def _pre_carregar_dados_temporada(db, season):
    logger.warning(f"Pre-carregando dados da temporada: {season}")

    resultados = db.query(PlayerGameStats, Game.date_start).join(Game, PlayerGameStats.game_id == Game.id).filter(Game.season == season, Game.status_short == 3, Game.stage != 1).order_by(PlayerGameStats.player_id, Game.date_start.asc()).all()

    dados_por_jogador = {}
    for stat, data_jogo in resultados:
        pid = stat.player_id
        if pid not in dados_por_jogador:
            dados_por_jogador[pid] = []

        item = {}
        item["points"] = float(stat.points or 0)
        item["assists"] = float(stat.assists or 0)
        item["tot_reb"] = float(stat.tot_reb or 0)
        item["steals"] = float(stat.steals or 0)
        item["blocks"] = float(stat.blocks or 0)
        item["minutes"] = _converter_minutos(stat.minutes)
        item["data"] = data_jogo
        dados_por_jogador[pid].append(item)

    logger.warning(f"Dados carregados: {len(dados_por_jogador)} jogadores, {len(resultados)} registros")
    return dados_por_jogador


def _extrair_features_em_memoria(jogos_jogador, stat_name):
    if len(jogos_jogador) < 5:
        return None, None

    lista_features = []
    lista_alvos = []

    for idx in range(5, len(jogos_jogador)):
        alvo = jogos_jogador[idx][stat_name]

        inicio_10 = max(0, idx - 10)
        inicio_3 = max(0, idx - 3)

        valores_10 = []
        for j in jogos_jogador[inicio_10:idx]:
            valores_10.append(j[stat_name])

        valores_3 = []
        for j in jogos_jogador[inicio_3:idx]:
            valores_3.append(j[stat_name])

        valores_minutos = []
        for j in jogos_jogador[inicio_10:idx]:
            valores_minutos.append(j["minutes"])

        todos_anteriores = []
        for j in jogos_jogador[:idx]:
            todos_anteriores.append(j[stat_name])

        if todos_anteriores:
            media_temporada = sum(todos_anteriores) / len(todos_anteriores)
        else:
            media_temporada = 0.0

        if valores_10:
            media_10 = sum(valores_10) / len(valores_10)
        else:
            media_10 = 0.0

        if valores_minutos:
            media_minutos = sum(valores_minutos) / len(valores_minutos)
        else:
            media_minutos = 0.0

        soma_pesos_3 = 0.0
        soma_ponderada_3 = 0.0
        for i in range(len(valores_3)):
            peso = i + 1
            soma_ponderada_3 = soma_ponderada_3 + (valores_3[i] * peso)
            soma_pesos_3 = soma_pesos_3 + peso
        if soma_pesos_3 > 0:
            ema_3 = soma_ponderada_3 / soma_pesos_3
        else:
            ema_3 = 0.0

        soma_pesos_10 = 0.0
        soma_ponderada_10 = 0.0
        for i in range(len(valores_10)):
            peso = i + 1
            soma_ponderada_10 = soma_ponderada_10 + (valores_10[i] * peso)
            soma_pesos_10 = soma_pesos_10 + peso
        if soma_pesos_10 > 0:
            ema_10 = soma_ponderada_10 / soma_pesos_10
        else:
            ema_10 = 0.0

        ema_ponderada = (ema_3 * 0.40) + (ema_10 * 0.35) + (media_temporada * 0.25)

        if len(valores_3) >= 2:
            eixo_x = np.arange(len(valores_3))
            inclinacao = float(np.polyfit(eixo_x, np.array(valores_3), 1)[0])
            variancia = float(np.std(valores_3))
        else:
            inclinacao = 0.0
            variancia = 0.0

        vetor = [ema_ponderada, 0, 0, 3, media_minutos, inclinacao, ema_ponderada, variancia, 0, media_temporada, media_10]
        lista_features.append(vetor)
        lista_alvos.append(alvo)

    if len(lista_features) < 5:
        return None, None

    return lista_features, lista_alvos


def retreinar_todos_modelos(db, season):
    limiar_minutos = config.MIN_MINUTOS_PALPITE
    dados_por_jogador = _pre_carregar_dados_temporada(db, season)

    ids_jogadores = []
    for pid in dados_por_jogador:
        jogos = dados_por_jogador[pid]
        if len(jogos) == 0:
            continue
        soma_minutos = 0.0
        for j in jogos:
            soma_minutos = soma_minutos + j["minutes"]
        media_minutos = soma_minutos / len(jogos)
        if media_minutos >= limiar_minutos:
            ids_jogadores.append(pid)

    total_jogadores = len(ids_jogadores)
    total_salvos = 0
    total_erros = 0

    logger.warning(f"Retreinamento iniciado: jogadores={total_jogadores}, temporada={season}")

    for player_id in ids_jogadores:
        jogos_jogador = dados_por_jogador[player_id]

        medias_temporada = {}
        for stat_name in STATS_PARA_TREINAR:
            soma = 0.0
            for j in jogos_jogador:
                soma = soma + j[stat_name]
            if len(jogos_jogador) > 0:
                medias_temporada[stat_name] = soma / len(jogos_jogador)
            else:
                medias_temporada[stat_name] = 0.0

        for stat_name in STATS_PARA_TREINAR:
            media = medias_temporada.get(stat_name, 0.0)
            limiar_stat = LIMIARES_TREINO.get(stat_name, 0.0)
            if media < limiar_stat:
                logger.debug(f"Treino ignorado (stat irrelevante): player_id={player_id}, stat={stat_name}, media={round(media, 2)}")
                continue
            try:
                lista_features, lista_alvos = _extrair_features_em_memoria(jogos_jogador, stat_name)
                modelo = _treinar_modelo_jogador(player_id=player_id, stat_name=stat_name, lista_features=lista_features, lista_alvos=lista_alvos)
                if modelo is None:
                    continue
                salvar_modelo(modelo=modelo, player_id=player_id, stat_name=stat_name)
                total_salvos = total_salvos + 1
            except Exception as erro:
                total_erros = total_erros + 1
                logger.warning(f"Erro ao treinar: player_id={player_id}, stat={stat_name}: {erro}")

    total_registros_db = 0
    for pid in dados_por_jogador:
        total_registros_db = total_registros_db + len(dados_por_jogador[pid])

    logger.warning(f"Retreinamento concluido: salvos={total_salvos}, erros={total_erros}, registros_db={total_registros_db}")

    resultado = {}
    resultado["total_salvos"] = total_salvos
    resultado["total_erros"] = total_erros
    resultado["total_jogadores_treino"] = total_jogadores
    resultado["total_registros_db"] = total_registros_db
    return resultado