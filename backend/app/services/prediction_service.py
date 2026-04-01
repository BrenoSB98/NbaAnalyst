import numpy as np

from app.db.models import PlayerGameStats, Game
from app.services import modelo_service
from app.services.analytics_service import calcular_medias_temporada_completa, calcular_medias_ultimos_n_jogos, calcular_medias_contra_time, calcular_defesa_adversaria_stat, calcular_dias_descanso

def converter_minutos_para_float(minutos_str):
    if not minutos_str or minutos_str == "":
        return 0.0

    try:
        texto = str(minutos_str)
        if ":" in texto:
            partes = texto.split(":")
            minutos = float(partes[0])
            segundos = 0.0
            if len(partes) > 1:
                segundos = float(partes[1])
            return minutos + (segundos / 60)
        else:
            return float(texto)
    except (ValueError, AttributeError):
        return 0.0

def calcular_media_ponderada_exponencial(valores):
    if not valores:
        return 0.0

    n = len(valores)
    soma_pesos = 0.0
    soma_ponderada = 0.0

    for i in range(n):
        peso = i + 1
        soma_ponderada = soma_ponderada + (valores[i] * peso)
        soma_pesos = soma_pesos + peso

    return round(soma_ponderada / soma_pesos, 4)

def _traduzir_chave_stat(stat_name):
    if stat_name == "tot_reb":
        return "rebounds"
    return stat_name

def prever_performance_jogador_heuristica(db, player_id, opponent_team_id, season, stat_name):
    media_temporada = calcular_medias_temporada_completa(db, player_id, season)
    media_ultimos_5 = calcular_medias_ultimos_n_jogos(db, player_id, n_games=5, season=season)
    media_contra_adversario = calcular_medias_contra_time(db, player_id, opponent_team_id, season)

    chave_averages = _traduzir_chave_stat(stat_name)

    valor_temporada = 0
    if media_temporada:
        averages = media_temporada.get("averages")
        if averages:
            valor_bruto = averages.get(chave_averages, 0)
            if valor_bruto:
                valor_temporada = valor_bruto

    valor_ultimos_5 = 0
    if media_ultimos_5:
        averages = media_ultimos_5.get("averages")
        if averages:
            valor_bruto = averages.get(chave_averages, 0)
            if valor_bruto:
                valor_ultimos_5 = valor_bruto

    valor_contra_adversario = 0
    if media_contra_adversario:
        averages = media_contra_adversario.get("averages")
        if averages:
            valor_bruto = averages.get(chave_averages, 0)
            if valor_bruto:
                valor_contra_adversario = valor_bruto

    peso_temporada  = 0.40
    peso_ultimos_5  = 0.40
    peso_adversario = 0.20
    previsao = (valor_temporada * peso_temporada) + (valor_ultimos_5 * peso_ultimos_5) + (valor_contra_adversario * peso_adversario)
    return round(previsao, 2)

def extrair_features_avancadas_jogador(db, player_id, season, stat_name):
    jogos_query = db.query(PlayerGameStats, Game).join(Game, PlayerGameStats.game_id == Game.id).filter(PlayerGameStats.player_id == player_id, Game.season == season, Game.status_short == 3).order_by(Game.date_start).all()

    if len(jogos_query) < 10:
        return None, None

    lista_features = []
    lista_alvos    = []
    for i in range(5, len(jogos_query)):
        ultimos_5_jogos = jogos_query[i - 5:i]

        valores_ultimos_5 = []
        for jogo_data in ultimos_5_jogos:
            valor_bruto = getattr(jogo_data[0], stat_name, 0)
            if valor_bruto is None:
                valor_bruto = 0
            valores_ultimos_5.append(float(valor_bruto))

        media_movel = calcular_media_ponderada_exponencial(valores_ultimos_5)

        jogo_atual = jogos_query[i]
        stat_atual = jogo_atual[0]
        game_atual = jogo_atual[1]

        time_jogador = stat_atual.team_id
        if game_atual.home_team_id == time_jogador:
            em_casa = 1
        else:
            em_casa = 0

        if em_casa == 1:
            id_adversario = game_atual.away_team_id
        else:
            id_adversario = game_atual.home_team_id

        defesa_adversaria = calcular_defesa_adversaria_stat(db, id_adversario, season, stat_name)
        dias_descanso = calcular_dias_descanso(db, player_id, game_atual.date_start, season)

        lista_minutos_ultimos_5 = []
        for jogo_data in ultimos_5_jogos:
            minutos_float = converter_minutos_para_float(jogo_data[0].minutes)
            lista_minutos_ultimos_5.append(minutos_float)

        if len(lista_minutos_ultimos_5) > 0:
            media_minutos = sum(lista_minutos_ultimos_5) / len(lista_minutos_ultimos_5)
        else:
            media_minutos = 0

        if len(valores_ultimos_5) >= 3:
            eixo_x     = np.arange(len(valores_ultimos_5))
            eixo_y     = np.array(valores_ultimos_5)
            inclinacao = np.polyfit(eixo_x, eixo_y, 1)[0]
        else:
            inclinacao = 0

        historico_adversario = calcular_medias_contra_time(db, player_id, id_adversario, season)
        media_vs_adversario  = media_movel
        if historico_adversario:
            averages = historico_adversario.get("averages")
            if averages:
                valor_hist = averages.get(stat_name, None)
                if valor_hist is not None:
                    media_vs_adversario = valor_hist

        vetor_feature = [media_movel, em_casa, defesa_adversaria, dias_descanso, media_minutos, inclinacao, media_vs_adversario]
        lista_features.append(vetor_feature)

        valor_alvo = getattr(stat_atual, stat_name, 0)
        if valor_alvo is None:
            valor_alvo = 0
        lista_alvos.append(float(valor_alvo))

    return lista_features, lista_alvos

def prever_performance_jogador_ml(db, player_id, opponent_team_id, season, stat_name, em_casa):
    modelo = modelo_service.carregar_modelo(player_id=player_id, stat_name=stat_name)

    if modelo is None:
        try:
            from xgboost import XGBRegressor
        except ImportError:
            try:
                from sklearn.ensemble import RandomForestRegressor as XGBRegressor
            except ImportError:
                return prever_performance_jogador_heuristica(db, player_id, opponent_team_id, season, stat_name)

        lista_features, lista_alvos = extrair_features_avancadas_jogador(db, player_id, season, stat_name)

        if lista_features is None or len(lista_features) < 10:
            return prever_performance_jogador_heuristica(db, player_id, opponent_team_id, season, stat_name)

        matriz_features = np.array(lista_features)
        vetor_alvos = np.array(lista_alvos)

        try:
            modelo = XGBRegressor(
                n_estimators=300,
                max_depth=4,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.7,
                min_child_weight=5,
                gamma=0.1,
                reg_alpha=0.1,
                reg_lambda=2.0,
                random_state=42,
                objective="reg:squarederror"
            )
        except TypeError:
            from sklearn.ensemble import RandomForestRegressor
            modelo = RandomForestRegressor(n_estimators=300, max_depth=5, min_samples_split=8, min_samples_leaf=4, random_state=42)

        modelo.fit(matriz_features, vetor_alvos)

    chave_averages = _traduzir_chave_stat(stat_name)
    media_ultimos_5_obj = calcular_medias_ultimos_n_jogos(db, player_id, n_games=5, season=season)
    media_ultimos_5_valor = 0
    media_minutos_valor  = 30

    if media_ultimos_5_obj:
        averages = media_ultimos_5_obj.get("averages")
        if averages:
            valor_bruto = averages.get(chave_averages, 0)
            if valor_bruto:
                media_ultimos_5_valor = valor_bruto
            minutos_bruto = averages.get("minutes", 30)
            if minutos_bruto:
                media_minutos_valor = minutos_bruto
    else:
        media_temporada_obj = calcular_medias_temporada_completa(db, player_id, season)
        if media_temporada_obj:
            averages = media_temporada_obj.get("averages")
            if averages:
                valor_bruto = averages.get(chave_averages, 0)
                if valor_bruto:
                    media_ultimos_5_valor = valor_bruto
                minutos_bruto = averages.get("minutes", 30)
                if minutos_bruto:
                    media_minutos_valor = minutos_bruto

    defesa_adversaria = calcular_defesa_adversaria_stat(db, opponent_team_id, season, stat_name)

    from datetime import datetime, timezone
    agora = datetime.now(timezone.utc)
    ultimo_jogo_jogador = db.query(Game).join(PlayerGameStats, PlayerGameStats.game_id == Game.id).filter(PlayerGameStats.player_id == player_id, Game.season == season, Game.status_short == 3).order_by(Game.date_start.desc()).first()

    if ultimo_jogo_jogador and ultimo_jogo_jogador.date_start:
        data_ultimo = ultimo_jogo_jogador.date_start
        if data_ultimo.tzinfo is None:
            from datetime import timezone as tz_mod
            data_ultimo = data_ultimo.replace(tzinfo=tz_mod.utc)
        delta = agora - data_ultimo
        dias_descanso_real = min(delta.days, 7)
    else:
        dias_descanso_real = 2

    ultimos_jogos = db.query(PlayerGameStats, Game).join(Game, PlayerGameStats.game_id == Game.id).filter(PlayerGameStats.player_id == player_id, Game.season == season, Game.status_short == 3).order_by(Game.date_start.desc()).limit(5).all()

    inclinacao_previsao = 0
    if len(ultimos_jogos) >= 3:
        valores_recentes = []
        for j in reversed(ultimos_jogos):
            valor_bruto = getattr(j[0], stat_name, 0)
            if valor_bruto is None:
                valor_bruto = 0
            valores_recentes.append(float(valor_bruto))

        eixo_x = np.arange(len(valores_recentes))
        eixo_y = np.array(valores_recentes)
        inclinacao_previsao = np.polyfit(eixo_x, eixo_y, 1)[0]

    media_vs_adversario = media_ultimos_5_valor
    historico_adversario = calcular_medias_contra_time(db, player_id, opponent_team_id, season)
    if historico_adversario:
        averages = historico_adversario.get("averages")
        if averages:
            valor_hist = averages.get(stat_name, None)
            if valor_hist is not None:
                media_vs_adversario = valor_hist

    vetor_previsao = np.array([[media_ultimos_5_valor, em_casa, defesa_adversaria, dias_descanso_real, media_minutos_valor, inclinacao_previsao, media_vs_adversario]])
    resultado      = modelo.predict(vetor_previsao)[0]
    return round(float(resultado), 2)

def prever_performance_jogador(db, player_id, opponent_team_id, season, stat_name, em_casa):
    return prever_performance_jogador_ml(db, player_id, opponent_team_id, season, stat_name, em_casa)

def prever_multiplas_stats_jogador(db, player_id, opponent_team_id, season, is_home):
    stats_para_prever = ["points", "assists", "tot_reb", "steals", "blocks"]

    previsoes = {}
    for stat_name in stats_para_prever:
        previsao = prever_performance_jogador(db, player_id, opponent_team_id, season, stat_name, is_home)

        if stat_name == "tot_reb":
            previsoes["rebounds"] = previsao
        else:
            previsoes[stat_name] = previsao
    return previsoes