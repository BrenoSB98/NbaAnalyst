import logging
import os

import numpy as np
from sqlalchemy import select

from app.config import config
from app.db.models import Game, GameTeamStats, PlayerGameStats, PlayerTeamSeason

logger = logging.getLogger(__name__)

STATS_PARA_TREINAR = ["points", "assists", "tot_reb", "steals", "blocks"]
PROPORCAO_TREINO = 0.7
TEMPORADAS_HISTORICAS = 1
MIN_AMOSTRAS_TREINO = 20

LIMIARES_TREINO = {}
LIMIARES_TREINO["points"] = 8.0
LIMIARES_TREINO["assists"] = 2.0
LIMIARES_TREINO["tot_reb"] = 3.5
LIMIARES_TREINO["steals"] = 0.9
LIMIARES_TREINO["blocks"] = 0.8

CONFIG_STATS = {}
CONFIG_STATS["points"] = {
    "n_estimators": 200,
    "max_depth": 5,
    "learning_rate": 0.05,
    "min_child_weight": 3,
    "subsample": 0.8,
    "colsample_bytree": 0.7,
    "gamma": 0.1,
    "reg_alpha": 0.1,
    "reg_lambda": 2.0,
}
CONFIG_STATS["assists"] = {
    "n_estimators": 150,
    "max_depth": 4,
    "learning_rate": 0.05,
    "min_child_weight": 4,
    "subsample": 0.8,
    "colsample_bytree": 0.7,
    "gamma": 0.1,
    "reg_alpha": 0.1,
    "reg_lambda": 2.0,
}
CONFIG_STATS["tot_reb"] = {
    "n_estimators": 150,
    "max_depth": 4,
    "learning_rate": 0.05,
    "min_child_weight": 4,
    "subsample": 0.8,
    "colsample_bytree": 0.7,
    "gamma": 0.1,
    "reg_alpha": 0.1,
    "reg_lambda": 2.0,
}
CONFIG_STATS["steals"] = {
    "n_estimators": 100,
    "max_depth": 3,
    "learning_rate": 0.05,
    "min_child_weight": 6,
    "subsample": 0.8,
    "colsample_bytree": 0.7,
    "gamma": 0.1,
    "reg_alpha": 0.1,
    "reg_lambda": 2.0,
}
CONFIG_STATS["blocks"] = {
    "n_estimators": 100,
    "max_depth": 3,
    "learning_rate": 0.05,
    "min_child_weight": 6,
    "subsample": 0.8,
    "colsample_bytree": 0.7,
    "gamma": 0.1,
    "reg_alpha": 0.1,
    "reg_lambda": 2.0,
}


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
            modelo = pickle.load(arquivo)
        logger.debug(f"Modelo carregado: player_id={player_id}, stat={stat_name}")
        return modelo
    except Exception as erro:
        logger.warning(
            f"Falha ao carregar modelo: player_id={player_id}, stat={stat_name}: {erro}"
        )
        return None


def _treinar_modelo_novo(lista_features, lista_alvos, stat_name):
    from xgboost import XGBRegressor

    matriz = np.array(lista_features)
    alvos = np.array(lista_alvos)
    cfg = CONFIG_STATS.get(stat_name, CONFIG_STATS["points"])
    modelo = XGBRegressor(
        n_estimators=cfg["n_estimators"],
        max_depth=cfg["max_depth"],
        learning_rate=cfg["learning_rate"],
        subsample=cfg["subsample"],
        colsample_bytree=cfg["colsample_bytree"],
        min_child_weight=cfg["min_child_weight"],
        gamma=cfg["gamma"],
        reg_alpha=cfg["reg_alpha"],
        reg_lambda=cfg["reg_lambda"],
        random_state=42,
        objective="reg:squarederror",
        n_jobs=-1,
    )
    modelo.fit(matriz, alvos)
    return modelo


def _treinar_modelo_jogador(player_id, stat_name, lista_features, lista_alvos):
    if lista_features is None or len(lista_features) < MIN_AMOSTRAS_TREINO:
        logger.debug(
            f"Amostras insuficientes para treinar: player_id={player_id}, stat={stat_name}, amostras={len(lista_features) if lista_features else 0}, minimo={MIN_AMOSTRAS_TREINO}"
        )
        return None
    logger.debug(
        f"Treinando: player_id={player_id}, stat={stat_name}, amostras={len(lista_features)}"
    )
    return _treinar_modelo_novo(lista_features, lista_alvos, stat_name)


def _listar_temporadas(temporada_atual):
    lista = []
    for delta in range(TEMPORADAS_HISTORICAS, -1, -1):
        lista.append(temporada_atual - delta)
    return lista


def _pre_carregar_dados_temporadas(db, temporadas):
    logger.info(f"Carregando dados das temporadas: {temporadas}")

    stmt = (
        select(PlayerGameStats, Game)
        .join(Game, PlayerGameStats.game_id == Game.id)
        .where(Game.season.in_(temporadas), Game.status_short == 3, Game.stage != 1)
        .order_by(PlayerGameStats.player_id, Game.date_start.asc())
    )

    resultados = db.execute(stmt).all()

    dados_por_jogador = {}
    for stat, jogo in resultados:
        pid = stat.player_id
        if pid not in dados_por_jogador:
            dados_por_jogador[pid] = []

        if stat.team_id == jogo.home_team_id:
            is_home = 1
            opponent_id = jogo.away_team_id
        else:
            is_home = 0
            opponent_id = jogo.home_team_id

        item = {}
        item["points"] = float(stat.points or 0)
        item["assists"] = float(stat.assists or 0)
        item["tot_reb"] = float(stat.tot_reb or 0)
        item["steals"] = float(stat.steals or 0)
        item["blocks"] = float(stat.blocks or 0)
        item["minutes"] = _converter_minutos(stat.minutes)
        item["fgp"] = float(stat.fgp or 0)
        item["ftp"] = float(stat.ftp or 0)
        item["fga"] = float(stat.fga or 0)
        item["fta"] = float(stat.fta or 0)
        item["turnovers"] = float(stat.turnovers or 0)
        if stat.pos:
            item["pos"] = stat.pos.split("-")[0]
        else:
            item["pos"] = None
        item["data"] = jogo.date_start
        item["is_home"] = is_home
        item["opponent_id"] = opponent_id
        item["season"] = jogo.season
        dados_por_jogador[pid].append(item)

    logger.info(
        f"Dados carregados: jogadores={len(dados_por_jogador)}, registros={len(resultados)}, temporadas={temporadas}"
    )
    return dados_por_jogador


def _pre_calcular_defesa_por_time(db, temporadas):
    logger.info(f"Calculando defesa por time: temporadas={temporadas}")
    mapa_defesa = {}
    for stat_name in STATS_PARA_TREINAR:
        mapa_defesa[stat_name] = {}

    stmt_stats = (
        select(PlayerGameStats, Game)
        .join(Game, PlayerGameStats.game_id == Game.id)
        .where(Game.season.in_(temporadas), Game.status_short == 3, Game.stage != 1)
    )

    resultados = db.execute(stmt_stats).all()

    acumulado = {}
    contagem_jogos = {}
    for stat, jogo in resultados:
        if stat.team_id == jogo.home_team_id:
            opponent_id = jogo.away_team_id
        else:
            opponent_id = jogo.home_team_id

        for stat_name in STATS_PARA_TREINAR:
            valor = float(getattr(stat, stat_name, 0) or 0)
            chave = (opponent_id, stat_name)
            if chave not in acumulado:
                acumulado[chave] = 0.0
                contagem_jogos[chave] = set()
            acumulado[chave] = acumulado[chave] + valor
            contagem_jogos[chave].add(jogo.id)

    for chave in acumulado:
        opponent_id, stat_name = chave
        n_jogos = len(contagem_jogos[chave])
        if n_jogos > 0:
            mapa_defesa[stat_name][opponent_id] = acumulado[chave] / n_jogos
        else:
            mapa_defesa[stat_name][opponent_id] = 0.0

    total_times = len(set(chave[0] for chave in acumulado))
    logger.info(
        f"Defesa calculada: times={total_times}, registros_processados={len(resultados)}"
    )
    return mapa_defesa


def _pre_calcular_defesa_por_posicao(db, temporadas):
    logger.info(f"Calculando defesa por posicao: temporadas={temporadas}")
    mapa = {}

    stmt_stats = (
        select(PlayerGameStats, Game)
        .join(Game, PlayerGameStats.game_id == Game.id)
        .where(Game.season.in_(temporadas), Game.status_short == 3, Game.stage != 1)
    )

    resultados = db.execute(stmt_stats).all()

    acumulado = {}
    contagem = {}
    for stat, jogo in resultados:
        if not stat.pos:
            continue
        pos = stat.pos.split("-")[0]
        if stat.team_id == jogo.home_team_id:
            opponent_id = jogo.away_team_id
        else:
            opponent_id = jogo.home_team_id

        for stat_name in STATS_PARA_TREINAR:
            valor = float(getattr(stat, stat_name, 0) or 0)
            chave = (opponent_id, pos, stat_name)
            if chave not in acumulado:
                acumulado[chave] = 0.0
                contagem[chave] = 0
            acumulado[chave] = acumulado[chave] + valor
            contagem[chave] = contagem[chave] + 1

    for chave in acumulado:
        if contagem[chave] > 0:
            mapa[chave] = acumulado[chave] / contagem[chave]
        else:
            mapa[chave] = 0.0

    logger.info(f"Defesa por posicao calculada: combinacoes={len(mapa)}")
    return mapa


def _pre_calcular_pace_por_time(db, temporadas):
    logger.info(f"Calculando pace por time: temporadas={temporadas}")
    mapa_pace = {}
    stmt = (
        select(GameTeamStats, Game)
        .join(Game, GameTeamStats.game_id == Game.id)
        .where(Game.season.in_(temporadas), Game.status_short == 3, Game.stage != 1)
    )

    resultados = db.execute(stmt).all()

    soma_pace = {}
    contagem = {}
    for team_stat, jogo in resultados:
        fga = float(team_stat.fga or 0)
        fta = float(team_stat.fta or 0)
        turnovers = float(team_stat.turnovers or 0)
        pace = fga + (0.44 * fta) + turnovers
        tid = team_stat.team_id
        if tid not in soma_pace:
            soma_pace[tid] = 0.0
            contagem[tid] = 0
        soma_pace[tid] = soma_pace[tid] + pace
        contagem[tid] = contagem[tid] + 1

    for tid in soma_pace:
        if contagem[tid] > 0:
            mapa_pace[tid] = soma_pace[tid] / contagem[tid]
        else:
            mapa_pace[tid] = 0.0

    logger.info(f"Pace calculado: times={len(mapa_pace)}")
    return mapa_pace


def _calcular_media_vs_adversario(jogos_anteriores, opponent_id, stat_name):
    valores = []
    for j in jogos_anteriores:
        if j["opponent_id"] == opponent_id:
            valores.append(j[stat_name])
    if not valores:
        return None
    soma = 0.0
    for v in valores:
        soma = soma + v
    return soma / len(valores)


def _extrair_features_em_memoria(
    jogos_jogador, stat_name, mapa_defesa, mapa_pace, mapa_defesa_posicao
):
    if len(jogos_jogador) < 5:
        return None, None

    qtd_treino = int(len(jogos_jogador) * PROPORCAO_TREINO)
    minimo_treino = MIN_AMOSTRAS_TREINO + 5
    if qtd_treino < minimo_treino:
        qtd_treino = min(minimo_treino, len(jogos_jogador))
    if qtd_treino < 5:
        return None, None

    lista_features = []
    lista_alvos = []

    for idx in range(5, qtd_treino):
        alvo = jogos_jogador[idx][stat_name]
        jogo_atual = jogos_jogador[idx]

        inicio_10 = max(0, idx - 10)
        inicio_5 = max(0, idx - 5)
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

        valores_fgp_5 = []
        for j in jogos_jogador[inicio_5:idx]:
            valores_fgp_5.append(j["fgp"])

        soma_fga = 0.0
        soma_fta = 0.0
        soma_tov = 0.0
        soma_min_usage = 0.0
        for j in jogos_jogador[inicio_10:idx]:
            soma_fga = soma_fga + j["fga"]
            soma_fta = soma_fta + j["fta"]
            soma_tov = soma_tov + j["turnovers"]
            soma_min_usage = soma_min_usage + j["minutes"]
        posses = soma_fga + (0.44 * soma_fta) + soma_tov
        if soma_min_usage > 0:
            usage_rate = round(posses / soma_min_usage, 3)
        else:
            usage_rate = 0.0

        todos_anteriores = []
        for j in jogos_jogador[:idx]:
            todos_anteriores.append(j[stat_name])

        if todos_anteriores:
            media_temporada = sum(todos_anteriores) / len(todos_anteriores)
        else:
            media_temporada = 0.0

        if valores_minutos:
            media_minutos = sum(valores_minutos) / len(valores_minutos)
        else:
            media_minutos = 0.0

        if valores_fgp_5:
            fgp_media_5 = sum(valores_fgp_5) / len(valores_fgp_5)
        else:
            fgp_media_5 = 0.0

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

        opponent_id = jogo_atual["opponent_id"]

        defesa_adversaria = mapa_defesa.get(stat_name, {}).get(opponent_id, 0.0)
        pace_adversario = mapa_pace.get(opponent_id, 0.0)

        media_vs_adv = _calcular_media_vs_adversario(
            jogos_jogador[:idx], opponent_id, stat_name
        )
        if media_vs_adv is None:
            media_vs_adv = ema_ponderada

        vetor = [
            ema_ponderada,
            media_temporada,
            media_minutos,
            defesa_adversaria,
            inclinacao,
            variancia,
            pace_adversario,
            fgp_media_5,
            usage_rate,
        ]
        lista_features.append(vetor)
        lista_alvos.append(alvo)

    if len(lista_features) < 5:
        return None, None

    return lista_features, lista_alvos


def _buscar_posicoes_jogadores(db, season, player_ids):
    mapa_posicao = {}
    if not player_ids:
        return mapa_posicao
    stmt = (
        select(PlayerTeamSeason)
        .where(
            PlayerTeamSeason.season == season,
            PlayerTeamSeason.player_id.in_(player_ids),
        )
        .order_by(PlayerTeamSeason.active.desc())
    )
    vinculos = db.execute(stmt).scalars().all()
    for vinculo in vinculos:
        pid = vinculo.player_id
        if pid in mapa_posicao:
            continue
        if not vinculo.pos:
            mapa_posicao[pid] = "N/D"
        else:
            mapa_posicao[pid] = vinculo.pos.split("-")[0]
    return mapa_posicao


def _contar_cobertura_por_posicao(mapa_posicao, player_ids_com_modelo):
    contagem = {}
    contagem["PG"] = 0
    contagem["SG"] = 0
    contagem["SF"] = 0
    contagem["PF"] = 0
    contagem["C"] = 0
    contagem["N/D"] = 0
    for pid in player_ids_com_modelo:
        pos = mapa_posicao.get(pid, "N/D")
        if pos in contagem:
            contagem[pos] = contagem[pos] + 1
        else:
            contagem["N/D"] = contagem["N/D"] + 1
    return contagem


def retreinar_todos_modelos(db, season):
    limiar_minutos = config.MIN_MINUTOS_PALPITE
    janela = config.JANELA_JOGOS_RECENTES
    temporadas = _listar_temporadas(season)

    dados_por_jogador = _pre_carregar_dados_temporadas(db, temporadas)
    mapa_defesa = _pre_calcular_defesa_por_time(db, temporadas)
    mapa_defesa_posicao = _pre_calcular_defesa_por_posicao(db, temporadas)
    mapa_pace = _pre_calcular_pace_por_time(db, temporadas)

    ids_jogadores = []
    for pid in dados_por_jogador:
        jogos = dados_por_jogador[pid]
        if len(jogos) == 0:
            continue
        jogos_recentes = jogos[-janela:]
        soma_minutos = 0.0
        for j in jogos_recentes:
            soma_minutos = soma_minutos + j["minutes"]
        media_minutos = soma_minutos / len(jogos_recentes)
        if media_minutos >= limiar_minutos:
            ids_jogadores.append(pid)

    total_jogadores = len(ids_jogadores)
    total_salvos = 0
    total_erros = 0
    jogadores_com_modelo = set()

    logger.info(
        f"Retreinamento iniciado: jogadores={total_jogadores}, temporadas={temporadas}, proporcao_treino={PROPORCAO_TREINO}, min_amostras={MIN_AMOSTRAS_TREINO}, janela_minutos={janela}, limiar_minutos={limiar_minutos}"
    )

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
                logger.debug(
                    f"Treino ignorado (stat irrelevante): player_id={player_id}, stat={stat_name}, media={round(media, 2)}"
                )
                continue
            try:
                lista_features, lista_alvos = _extrair_features_em_memoria(
                    jogos_jogador,
                    stat_name,
                    mapa_defesa,
                    mapa_pace,
                    mapa_defesa_posicao,
                )
                modelo = _treinar_modelo_jogador(
                    player_id=player_id,
                    stat_name=stat_name,
                    lista_features=lista_features,
                    lista_alvos=lista_alvos,
                )
                if modelo is None:
                    continue
                salvar_modelo(modelo=modelo, player_id=player_id, stat_name=stat_name)
                total_salvos = total_salvos + 1
                jogadores_com_modelo.add(player_id)
            except Exception as erro:
                total_erros = total_erros + 1
                logger.error(
                    f"Erro ao treinar: player_id={player_id}, stat={stat_name}: {erro}"
                )

    total_registros_db = 0
    for pid in dados_por_jogador:
        total_registros_db = total_registros_db + len(dados_por_jogador[pid])

    logger.info(
        f"Retreinamento concluido: salvos={total_salvos}, erros={total_erros}, registros_db={total_registros_db}"
    )
    if total_erros > 0:
        logger.warning(
            f"Retreinamento concluido com {total_erros} erro(s): verifique os logs de erro acima"
        )

    mapa_posicao = _buscar_posicoes_jogadores(db, season, list(jogadores_com_modelo))
    cobertura_posicao = _contar_cobertura_por_posicao(
        mapa_posicao, jogadores_com_modelo
    )

    resultado = {}
    resultado["total_salvos"] = total_salvos
    resultado["total_erros"] = total_erros
    resultado["total_jogadores_treino"] = total_jogadores
    resultado["total_jogadores_com_modelo"] = len(jogadores_com_modelo)
    resultado["total_registros_db"] = total_registros_db
    resultado["cobertura_posicao"] = cobertura_posicao
    resultado["temporadas"] = temporadas
    resultado["proporcao_treino"] = PROPORCAO_TREINO
    resultado["limiar_minutos"] = limiar_minutos
    resultado["min_amostras"] = MIN_AMOSTRAS_TREINO
    resultado["limiares_treino"] = dict(LIMIARES_TREINO)
    return resultado
