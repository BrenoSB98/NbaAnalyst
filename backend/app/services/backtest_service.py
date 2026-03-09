from sqlalchemy.orm import Session
from app.db.models import PlayerGameStats, Game
from app.services.analytics_service import calcular_defesa_adversaria_stat, calcular_dias_descanso
from app.services.prediction_service import extrair_features_avancadas_jogador, converter_minutos_para_float, prever_performance_jogador_heuristica
import numpy as np

def backtest_jogador(db: Session, player_id: int, season: int, stat_name: str = "points", limit_games: int = 10):
    jogos_reais = (db.query(PlayerGameStats, Game).join(Game, PlayerGameStats.game_id == Game.id)
                   .filter(PlayerGameStats.player_id == player_id, Game.season == season, Game.status_short == 3).order_by(Game.date_start.asc()).all())

    if len(jogos_reais) < 10:
        return {"error": "Dados insuficientes para backtest. É necessário pelo menos 10 jogos completos."}

    features, targets = extrair_features_avancadas_jogador(db, player_id, season, stat_name)
    modelo = None
    if features is not None and len(features) >= 10:
        X = np.array(features)
        y = np.array(targets)
        try:
            from xgboost import XGBRegressor
            modelo = XGBRegressor(n_estimators=150, max_depth=6, learning_rate=0.1, random_state=42, objective='reg:squarederror')
        except ImportError:
            from sklearn.ensemble import RandomForestRegressor
            modelo = RandomForestRegressor(n_estimators=150, max_depth=8, random_state=42)
        modelo.fit(X, y)

    resultados = []
    erros_absolutos = []

    for i in range(5, len(jogos_reais)):
        stat_real_obj, jogo_obj = jogos_reais[i]
        valor_real = float(getattr(stat_real_obj, stat_name, 0) or 0)

        is_home = 1 if jogo_obj.home_team_id == stat_real_obj.team_id else 0
        opponent_id = jogo_obj.away_team_id if is_home else jogo_obj.home_team_id

        if modelo is not None:
            ultimos_5 = jogos_reais[max(0, i - 5):i]
            valores_ultimos_5 = [float(getattr(j[0], stat_name, 0) or 0) for j in ultimos_5]
            media_movel = sum(valores_ultimos_5) / len(valores_ultimos_5) if valores_ultimos_5 else 0

            defesa_adversaria = calcular_defesa_adversaria_stat(db, opponent_id, season, stat_name)
            dias_descanso = calcular_dias_descanso(db, player_id, jogo_obj.date_start, season)

            minutos_ultimos_5 = [converter_minutos_para_float(j[0].minutes) for j in ultimos_5]
            media_minutos = sum(minutos_ultimos_5) / len(minutos_ultimos_5) if minutos_ultimos_5 else 0

            if len(valores_ultimos_5) >= 3:
                x = np.arange(len(valores_ultimos_5))
                slope = np.polyfit(x, np.array(valores_ultimos_5), 1)[0]
            else:
                slope = 0

            feature_previsao = np.array([[media_movel, is_home, defesa_adversaria, dias_descanso, media_minutos, slope, media_movel]])
            predicao = round(float(modelo.predict(feature_previsao)[0]), 2)
        else:
            predicao = prever_performance_jogador_heuristica(db, player_id, opponent_id, season, stat_name)

        erro = abs(predicao - valor_real)
        erros_absolutos.append(erro)
        resultados.append({
            "game_id": jogo_obj.id,
            "date": jogo_obj.date_start,
            "real": valor_real,
            "predicao": predicao,
            "erro_absoluto": round(erro, 2),
        })

    if erros_absolutos:
        mae = round(np.mean(erros_absolutos), 2) 
    else:
        mae = 0

    return {
        "player_id": player_id,
        "stat": stat_name,
        "season": season,
        "mean_absolute_error": mae,
        "total_tests": len(resultados),
        "detailed_results": resultados[-limit_games:],
    }