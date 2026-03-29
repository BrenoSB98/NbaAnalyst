import os
import pickle
import logging
import numpy as np

from app.config import config
from app.db.models import PlayerGameStats, PlayerTeamSeason

logger = logging.getLogger("modelo_service")

STATS_PARA_TREINAR = ["points", "assists", "tot_reb", "steals", "blocks"]

def _converter_minutos_modelo(minutos_str):
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
    nome_arquivo = f"modelo_{player_id}_{stat_name}.pkl"
    return os.path.join(pasta, nome_arquivo)


def salvar_modelo(modelo, player_id, stat_name):
    pasta = config.PASTA_MODELOS

    if not os.path.exists(pasta):
        os.makedirs(pasta)

    caminho = _caminho_modelo(player_id, stat_name)

    with open(caminho, "wb") as arquivo:
        pickle.dump(modelo, arquivo)


def carregar_modelo(player_id, stat_name):
    caminho = _caminho_modelo(player_id, stat_name)

    if not os.path.exists(caminho):
        return None

    try:
        with open(caminho, "rb") as arquivo:
            modelo = pickle.load(arquivo)
        return modelo
    except Exception as erro:
        logger.warning(f"Falha ao carregar modelo do disco —> player_id={player_id}, stat={stat_name}: {erro}")
        return None


def _treinar_modelo_jogador(db, player_id, season, stat_name):
    from app.services.prediction_service import extrair_features_avancadas_jogador

    lista_features, lista_alvos = extrair_features_avancadas_jogador(db, player_id, season, stat_name)

    if lista_features is None or len(lista_features) < 10:
        return None

    matriz_features = np.array(lista_features)
    vetor_alvos = np.array(lista_alvos)

    try:
        from xgboost import XGBRegressor
        modelo = XGBRegressor(n_estimators=150, learning_rate=0.1, subsample=0.8, colsample_bytree=0.8, random_state=42, objective="reg:squarederror")
    except ImportError:
        from sklearn.ensemble import RandomForestRegressor
        modelo = RandomForestRegressor(n_estimators=150, max_depth=8, min_samples_split=5, random_state=42)

    modelo.fit(matriz_features, vetor_alvos)
    return modelo

def retreinar_todos_modelos(db, season):
    limiar = config.MIN_MINUTOS_PALPITE

    stats_jogadores = db.query(PlayerGameStats).filter(PlayerGameStats.season == season).all()

    soma_minutos = {}
    contagem_jogos = {}

    for stat in stats_jogadores:
        pid = stat.player_id
        minutos = _converter_minutos_modelo(stat.minutes)

        if pid not in soma_minutos:
            soma_minutos[pid] = 0.0
            contagem_jogos[pid] = 0

        soma_minutos[pid] = soma_minutos[pid] + minutos
        contagem_jogos[pid] = contagem_jogos[pid] + 1

    ids_jogadores = []
    for pid in soma_minutos:
        if contagem_jogos[pid] == 0:
            continue
        media = soma_minutos[pid] / contagem_jogos[pid]
        if media >= limiar:
            ids_jogadores.append(pid)

    total_jogadores = len(ids_jogadores)
    total_modelos_salvos = 0
    total_erros = 0

    logger.warning(f"Iniciando retreinamento —> jogadores={total_jogadores}, temporada={season}, limiar_minutos={limiar}")

    for player_id in ids_jogadores:
        for stat_name in STATS_PARA_TREINAR:
            try:
                modelo = _treinar_modelo_jogador(db=db, player_id=player_id, season=season, stat_name=stat_name)

                if modelo is None:
                    continue

                salvar_modelo(modelo=modelo, player_id=player_id, stat_name=stat_name)
                total_modelos_salvos = total_modelos_salvos + 1

            except Exception as erro:
                total_erros = total_erros + 1
                logger.warning(f"Erro ao retreinar modelo —> player_id={player_id}, stat={stat_name}: {erro}")

    logger.warning(f"Retreinamento concluido —> modelos_salvos={total_modelos_salvos}, erros={total_erros}, temporada={season}")
    return total_modelos_salvos