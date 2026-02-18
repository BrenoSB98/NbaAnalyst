from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import PlayerGameStats, Game
from app.services.analytics import calcular_medias_temporada_completa, calcular_medias_ultimos_n_jogos, calcular_medias_contra_time, calcular_defesa_adversaria_stat, calcular_dias_descanso
import numpy as np
from datetime import datetime

def converter_minutos_para_float(minutos_str):
    if not minutos_str or minutos_str == "":
        return 0.0
    
    try:
        if ":" in str(minutos_str):
            partes = str(minutos_str).split(":")
            minutos = float(partes[0])
            segundos = float(partes[1]) if len(partes) > 1 else 0
            return minutos + (segundos / 60)
        else:
            return float(minutos_str)
    except (ValueError, AttributeError):
        return 0.0
    
def prever_performance_jogador_heuristica(db, player_id, opponent_team_id, season, stat_name="points"):
    media_temporada = calcular_medias_temporada_completa(db, player_id, season)
    media_ultimos_5 = calcular_medias_ultimos_n_jogos(db, player_id, n_games=5, season=season)
    media_contra_adversario = calcular_medias_contra_time(db, player_id, opponent_team_id, season)

    valor_temporada = 0
    if media_temporada and media_temporada.get("averages"):
        valor_temporada = media_temporada["averages"].get(stat_name, 0)

    valor_ultimos_5 = 0
    if media_ultimos_5 and media_ultimos_5.get("averages"):
        valor_ultimos_5 = media_ultimos_5["averages"].get(stat_name, 0)

    valor_contra_adversario = 0
    if media_contra_adversario and media_contra_adversario.get("averages"):
        valor_contra_adversario = media_contra_adversario["averages"].get(stat_name, 0)

    peso_temporada = 0.40
    peso_ultimos_5 = 0.40
    peso_adversario = 0.20

    previsao = ((valor_temporada * peso_temporada) + (valor_ultimos_5 * peso_ultimos_5) + (valor_contra_adversario * peso_adversario))
    return round(previsao, 2)

def extrair_features_avancadas_jogador(db, player_id, season, stat_name):
    jogos_query = (db.query(PlayerGameStats, Game).join(Game, PlayerGameStats.game_id == Game.id)
                   .filter(PlayerGameStats.player_id == player_id, Game.season == season, Game.status_short == 3)
                   .order_by(Game.date_start).all()
                   )
    if len(jogos_query) < 10:
        return None, None

    features = []
    targets = []
    for i in range(5, len(jogos_query)):
        ultimos_5_jogos = jogos_query[i-5:i]
        valores_ultimos_5 = [float(getattr(jogo_data[0], stat_name, 0) or 0) for jogo_data in ultimos_5_jogos]
        media_movel = sum(valores_ultimos_5) / len(valores_ultimos_5)

        jogo_atual = jogos_query[i]
        stat_atual = jogo_atual[0]
        game_atual = jogo_atual[1]

        time_jogador = stat_atual.team_id
        is_home = 1 if game_atual.home_team_id == time_jogador else 0

        adversario_id = game_atual.away_team_id if is_home else game_atual.home_team_id
        defesa_adversaria = calcular_defesa_adversaria_stat(db, adversario_id, season, stat_name)
        dias_descanso = calcular_dias_descanso(db, player_id, game_atual.date_start, season)

        minutos_ultimos_5 = [converter_minutos_para_float(jogo_data[0].minutes) for jogo_data in ultimos_5_jogos]
        media_minutos = sum(minutos_ultimos_5) / len(minutos_ultimos_5) if minutos_ultimos_5 else 0

        if len(valores_ultimos_5) >= 3:
            x = np.arange(len(valores_ultimos_5))
            y = np.array(valores_ultimos_5)
            slope = np.polyfit(x, y, 1)[0]
        else:
            slope = 0

        historico_adversario = calcular_medias_contra_time(db, player_id, adversario_id, season)
        if historico_adversario and historico_adversario.get("averages"):
            media_vs_adversario = historico_adversario["averages"].get(stat_name, media_movel)
        else:
            media_vs_adversario = media_movel

        feature_vector = [media_movel, is_home, defesa_adversaria, dias_descanso, media_minutos, slope, media_vs_adversario]
        features.append(feature_vector)

        valor_target = float(getattr(stat_atual, stat_name, 0) or 0)
        targets.append(valor_target)
    return features, targets

def prever_performance_jogador_ml(db, player_id, opponent_team_id, season, stat_name="points", is_home=1):
    try:
        from xgboost import XGBRegressor
    except ImportError:
        try:
            from sklearn.ensemble import RandomForestRegressor as XGBRegressor
        except ImportError:
            return prever_performance_jogador_heuristica(db, player_id, opponent_team_id, season, stat_name)
    features, targets = extrair_features_avancadas_jogador(db, player_id, season, stat_name)

    if features is None or len(features) < 10:
        return prever_performance_jogador_heuristica(db, player_id, opponent_team_id, season, stat_name)

    X = np.array(features)
    y = np.array(targets)

    try:
        modelo = XGBRegressor(n_estimators=150, max_depth=6, learning_rate=0.1, subsample=0.8, colsample_bytree=0.8, random_state=42, objective='reg:squarederror')
    except TypeError:
        from sklearn.ensemble import RandomForestRegressor
        modelo = RandomForestRegressor(n_estimators=150, max_depth=8, min_samples_split=5, random_state=42)    
    modelo.fit(X, y)

    media_ultimos_5_obj = calcular_medias_ultimos_n_jogos(db, player_id, n_games=5, season=season)
    if media_ultimos_5_obj and media_ultimos_5_obj.get("averages"):
        media_ultimos_5_valor = media_ultimos_5_obj["averages"].get(stat_name, 0)
        media_minutos_valor = media_ultimos_5_obj["averages"].get("minutes", 30)
    else:
        media_temporada_obj = calcular_medias_temporada_completa(db, player_id, season)
        if media_temporada_obj and media_temporada_obj.get("averages"):
            media_ultimos_5_valor = media_temporada_obj["averages"].get(stat_name, 0)
            media_minutos_valor = media_temporada_obj["averages"].get("minutes", 30)
        else:
            media_ultimos_5_valor = 0
            media_minutos_valor = 30

    defesa_adversaria = calcular_defesa_adversaria_stat(db, opponent_team_id, season, stat_name)
    previsao_dias_descanso = 2

    ultimos_jogos = (db.query(PlayerGameStats, Game).join(Game, PlayerGameStats.game_id == Game.id)
                     .filter(PlayerGameStats.player_id == player_id, Game.season == season, Game.status_short == 3)
                     .order_by(Game.date_start.desc()).limit(5).all()
                     )
    
    if len(ultimos_jogos) >= 3:
        valores_recentes = [float(getattr(j[0], stat_name, 0) or 0) for j in reversed(ultimos_jogos)]
        x = np.arange(len(valores_recentes))
        y_vals = np.array(valores_recentes)
        slope_previsao = np.polyfit(x, y_vals, 1)[0]
    else:
        slope_previsao = 0

    historico_adversario = calcular_medias_contra_time(db, player_id, opponent_team_id, season)
    if historico_adversario and historico_adversario.get("averages"):
        media_vs_adversario = historico_adversario["averages"].get(stat_name, media_ultimos_5_valor)
    else:
        media_vs_adversario = media_ultimos_5_valor

    feature_previsao = np.array([[media_ultimos_5_valor, is_home, defesa_adversaria, previsao_dias_descanso, media_minutos_valor, slope_previsao, media_vs_adversario]])
    previsao = modelo.predict(feature_previsao)[0]
    return round(float(previsao), 2)

def prever_performance_jogador(db, player_id, opponent_team_id, season, stat_name="points", is_home=1):
    return prever_performance_jogador_ml(db, player_id, opponent_team_id, season, stat_name, is_home)

def prever_multiplas_stats_jogador(db, player_id, opponent_team_id, season, is_home=1):
    stats_para_prever = ["points", "assists", "tot_reb", "steals", "blocks"]

    previsoes = {}
    for stat_name in stats_para_prever:
        previsao = prever_performance_jogador(db, player_id, opponent_team_id, season, stat_name, is_home)

        if stat_name == "tot_reb":
            previsoes["rebounds"] = previsao
        else:
            previsoes[stat_name] = previsao
    return previsoes