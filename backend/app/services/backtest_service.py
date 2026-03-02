from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.db.models import PlayerGameStats, Game
from app.services.prediction_service import prever_performance_jogador
import numpy as np

def executar_backtest_jogador(db: Session, player_id: int, season: int, stat_name: str = "points", limit_games: int = 10):
    jogos_reais = (db.query(PlayerGameStats, Game).join(Game, PlayerGameStats.game_id == Game.id)
                   .filter(PlayerGameStats.player_id == player_id, Game.season == season, Game.status_short == 3).order_by(Game.date_start.asc()).all())

    if len(jogos_reais) < 5:
        return {"error": "Dados insuficientes para backtest"}

    resultados = []
    erros_absolutos = []

    for i in range(5, len(jogos_reais)):
        stat_real_obj, jogo_obj = jogos_reais[i]
        
        valor_real = float(getattr(stat_real_obj, stat_name, 0) or 0)
        
        is_home = 1 if jogo_obj.home_team_id == stat_real_obj.team_id else 0
        opponent_id = jogo_obj.away_team_id if is_home else jogo_obj.home_team_id

        predicao = prever_performance_jogador(db, player_id, opponent_id, season, stat_name, is_home)
        erro = abs(predicao - valor_real)
        erros_absolutos.append(erro)

        resultado_jogo = {
            "game_id": jogo_obj.id,
            "date": jogo_obj.date_start,
            "real": valor_real,
            "predicao": predicao,
            "erro_absoluto": round(erro, 2)
        }
        resultados.append(resultado_jogo)

    mae = 0
    if len(erros_absolutos) > 0:
        soma_erros = sum(erros_absolutos)
        mae = round(soma_erros / len(erros_absolutos), 2)

    return {
        "player_id": player_id,
        "stat": stat_name,
        "season": season,
        "mean_absolute_error": mae,
        "total_tests": len(resultados),
        "detailed_results": resultados[-limit_games:]
    }