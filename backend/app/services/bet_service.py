import statistics
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.db.models import Player, Team, Game, PlayerGameStats
from app.services.prediction_service import prever_performance_jogador
from app.services.analytics_service import calcular_medias_temporada_completa, calcular_medias_ultimos_n_jogos

def calcular_coeficiente_variacao(db: Session, player_id: int, season: int, stat_name: str):
    estatistica = (db.query(PlayerGameStats).join(Game, PlayerGameStats.game_id == Game.id)
             .filter(PlayerGameStats.player_id == player_id, Game.season == season, Game.status_short == 3).all())
    
    if len(estatistica) < 5:
        return None
    
    valores = [float(getattr(estat, stat_name, 0) or 0) for estat in estatistica]    
    if not valores or sum(valores) == 0:
        return None
    
    media = statistics.mean(valores)    
    if media == 0:
        return None
    
    desvio_padrao = statistics.stdev(valores) if len(valores) > 1 else 0
    cv = (desvio_padrao / media) * 100
    
    return {
        "mean": round(media, 2),
        "std_dev": round(desvio_padrao, 2),
        "coefficient_variation": round(cv, 2),
        "consistency_rating": "Alta" if cv < 30 else "Média" if cv < 50 else "Baixa",
        "sample_size": len(valores)
    }

def identificar_oportunidades_over_under(db: Session, season: int, stat_name: str = "points", min_games: int = 10, threshold_percentage: float = 15.0, limit: int = 10):
    data_limite = datetime.now() - timedelta(days=7)
    
    jogos_recentes = (db.query(Game).filter(Game.season == season,  Game.status_short == 3, Game.date_start >= data_limite)
                      .order_by(Game.date_start.desc()).limit(50).all()
                      )
    
    oportunidades = []    
    for jogo in jogos_recentes:
        for team_id, opponent_id, is_home in [(jogo.home_team_id, jogo.away_team_id, 1), (jogo.away_team_id, jogo.home_team_id, 0)]:
            jogadores_stats = (db.query(PlayerGameStats).join(Game, PlayerGameStats.game_id == Game.id)
                               .filter(PlayerGameStats.team_id == team_id, Game.season == season, Game.status_short == 3)
                               .group_by(PlayerGameStats.player_id).having(func.count(PlayerGameStats.game_id) >= min_games)
                               .with_entities(PlayerGameStats.player_id).distinct().all()
                               )
            
            for (player_id,) in jogadores_stats:
                media_temporada = calcular_medias_temporada_completa(db, player_id, season)                
                if not media_temporada or not media_temporada.get("averages"):
                    continue
                
                media_stat = media_temporada["averages"].get(stat_name, 0)                
                if media_stat == 0:
                    continue
                
                try:
                    predicao = prever_performance_jogador(db, player_id, opponent_id, season, stat_name, is_home)
                except Exception:
                    continue
                
                diferenca = predicao - media_stat
                diferenca_percentual = abs((diferenca / media_stat) * 100)                
                if diferenca_percentual < threshold_percentage:
                    continue
                
                consistencia = calcular_coeficiente_variacao(db, player_id, season, stat_name)                
                if not consistencia:
                    continue
                
                jogador = db.query(Player).filter(Player.id == player_id).first()
                time = db.query(Team).filter(Team.id == team_id).first()
                adversario = db.query(Team).filter(Team.id == opponent_id).first()
                
                if not jogador or not time or not adversario:
                    continue
                
                bet_type = "OVER" if diferenca > 0 else "UNDER"                
                consistency_bonus = 1.5 if consistencia["coefficient_variation"] < 30 else 1.0
                edge = diferenca_percentual * consistency_bonus
                
                oportunidade = {
                    "player_id": player_id,
                    "player_name": f"{jogador.firstname} {jogador.lastname}",
                    "team": time.name,
                    "opponent": adversario.name,
                    "game_id": jogo.id,
                    "game_date": jogo.date_start.isoformat(),
                    "is_home": bool(is_home),
                    "stat": stat_name,
                    "season_average": round(media_stat, 2),
                    "prediction": predicao,
                    "difference": round(diferenca, 2),
                    "difference_percentage": round(diferenca_percentual, 2),
                    "bet_type": bet_type,
                    "edge": round(edge, 2),
                    "consistency": consistencia["consistency_rating"],
                    "coefficient_variation": consistencia["coefficient_variation"],
                    "confidence": "Alta" if edge > 25 else "Média" if edge > 15 else "Baixa"
                }                
                oportunidades.append(oportunidade)

    oportunidades_ordenadas = sorted(oportunidades, key=lambda x: x["edge"], reverse=True)    
    return oportunidades_ordenadas[:limit]

def identificar_high_confidence_bets(db: Session, season: int, stat_name: str = "points", max_cv: float = 30.0, min_games: int = 15, limit: int = 10):
    jogadores_ativos = (db.query(PlayerGameStats.player_id).join(Game, PlayerGameStats.game_id == Game.id)
                        .filter(Game.season == season, Game.status_short == 3).group_by(PlayerGameStats.player_id)
                        .having(func.count(PlayerGameStats.game_id) >= min_games).all()
                        )
    
    high_confidence = []    
    for (player_id,) in jogadores_ativos:
        consistencia = calcular_coeficiente_variacao(db, player_id, season, stat_name)        
        if not consistencia or consistencia["coefficient_variation"] > max_cv:
            continue
        
        ultimo_jogo = (db.query(PlayerGameStats, Game).join(Game, PlayerGameStats.game_id == Game.id)
                       .filter(PlayerGameStats.player_id == player_id, Game.season == season, Game.status_short == 3)
                       .order_by(Game.date_start.desc()).first()
                       )
        
        if not ultimo_jogo:
            continue
        
        stat_ultimo = ultimo_jogo[0]
        game_ultimo = ultimo_jogo[1]
        
        is_home = game_ultimo.home_team_id == stat_ultimo.team_id
        opponent_id = game_ultimo.away_team_id if is_home else game_ultimo.home_team_id
        
        try:
            predicao = prever_performance_jogador(db, player_id, opponent_id, season, stat_name, is_home)
        except Exception:
            continue
        
        jogador = db.query(Player).filter(Player.id == player_id).first()
        time = db.query(Team).filter(Team.id == stat_ultimo.team_id).first()
        
        if not jogador or not time:
            continue
        
        media_temporada = calcular_medias_temporada_completa(db, player_id, season)
        media_stat = media_temporada["averages"].get(stat_name, 0) if media_temporada else 0
        
        high_confidence.append({
            "player_id": player_id,
            "player_name": f"{jogador.firstname} {jogador.lastname}",
            "team": time.name,
            "stat": stat_name,
            "season_average": round(media_stat, 2),
            "predicted_next_game": predicao,
            "consistency_rating": consistencia["consistency_rating"],
            "coefficient_variation": consistencia["coefficient_variation"],
            "std_dev": consistencia["std_dev"],
            "games_played": consistencia["sample_size"],
            "confidence_score": round(100 - consistencia["coefficient_variation"], 2)
        })
    
    high_confidence_ordenado = sorted(high_confidence, key=lambda x: x["confidence_score"], reverse=True)    
    return high_confidence_ordenado[:limit]


def analisar_tendencias_jogador(db: Session, player_id: int, season: int, stat_name: str = "points"):
    ultimos_jogos = (db.query(PlayerGameStats, Game).join(Game, PlayerGameStats.game_id == Game.id)
                     .filter(PlayerGameStats.player_id == player_id, Game.season == season, Game.status_short == 3)
                     .order_by(Game.date_start.desc()).limit(10).all()
                     )
    
    if len(ultimos_jogos) < 5:
        return None
    
    valores = [float(getattr(jogo[0], stat_name, 0) or 0) for jogo in reversed(ultimos_jogos)]
    media_ultimos_3 = sum(valores[-3:]) / 3 if len(valores) >= 3 else 0
    media_ultimos_5 = sum(valores[-5:]) / 5 if len(valores) >= 5 else 0
    media_ultimos_10 = sum(valores) / len(valores)
    
    if media_ultimos_3 > media_ultimos_5 > media_ultimos_10:
        tendencia = "Em Alta"
        tendencia_score = 3
    elif media_ultimos_3 > media_ultimos_5:
        tendencia = "Subindo"
        tendencia_score = 2
    elif media_ultimos_3 < media_ultimos_5 < media_ultimos_10:
        tendencia = "Em Queda"
        tendencia_score = -3
    elif media_ultimos_3 < media_ultimos_5:
        tendencia = "Caindo"
        tendencia_score = -2
    else:
        tendencia = "Estável"
        tendencia_score = 0
    
    jogador = db.query(Player).filter(Player.id == player_id).first()
    
    return {
        "player_id": player_id,
        "player_name": f"{jogador.firstname} {jogador.lastname}" if jogador else "Desconhecido",
        "stat": stat_name,
        "trend": tendencia,
        "trend_score": tendencia_score,
        "avg_last_3": round(media_ultimos_3, 2),
        "avg_last_5": round(media_ultimos_5, 2),
        "avg_last_10": round(media_ultimos_10, 2),
        "recent_values": valores[-5:],
        "games_analyzed": len(ultimos_jogos)
    }