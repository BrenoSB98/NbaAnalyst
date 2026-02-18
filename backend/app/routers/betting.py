from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.db_utils import get_db
from app.services.betting_service import identificar_oportunidades_over_under, identificar_high_confidence_bets, analisar_tendencias_jogador, calcular_coeficiente_variacao

router = APIRouter()

@router.get("/over-under")
def get_over_under_opportunities(season: int = Query(), stat_name: str = Query("points"), min_games: int = Query(10), threshold: float = Query(15.0), limit: int = Query(10), db: Session = Depends(get_db)):
    try:
        oportunidades = identificar_oportunidades_over_under(db=db, season=season, stat_name=stat_name, min_games=min_games, threshold_percentage=threshold, limit=limit)
        
        return {
            "season": season,
            "stat": stat_name,
            "threshold_percentage": threshold,
            "total_opportunities": len(oportunidades),
            "bet": oportunidades
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar oportunidades: {str(e)}")

@router.get("/high-confidence")
def get_high_confidence_bets(season: int = Query(), stat_name: str = Query(), max_cv: float = Query(), min_games: int = Query(), limit: int = Query(), db: Session = Depends(get_db)):
    try:
        high_confidence = identificar_high_confidence_bets(db=db, season=season, stat_name=stat_name, max_cv=max_cv, min_games=min_games, limit=limit)
        
        return {
            "season": season,
            "stat": stat_name,
            "max_coefficient_variation": max_cv,
            "total_players": len(high_confidence),
            "high_confidence_bets": high_confidence
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar apostas de alta confiança: {str(e)}")

@router.get("/player/{player_id}/trend")
def get_player_trend(player_id: int, season: int = Query(), stat_name: str = Query(), db: Session = Depends(get_db)):
    try:
        tendencia = analisar_tendencias_jogador(db=db, player_id=player_id, season=season, stat_name=stat_name)
        
        if not tendencia:
            raise HTTPException(status_code=404, detail=f"Dados insuficientes para análise de tendência (mínimo 5 jogos)")        
        return tendencia
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao analisar tendência: {str(e)}")

@router.get("/player/{player_id}/consistency")
def get_player_consistency(player_id: int, season: int = Query(), stat_name: str = Query(), db: Session = Depends(get_db)):
    try:
        consistencia = calcular_coeficiente_variacao(db=db, player_id=player_id, season=season, stat_name=stat_name)        
        if not consistencia:
            raise HTTPException(status_code=404, detail=f"Dados insuficientes para calcular consistência (mínimo 5 jogos)")
        
        return {
            "player_id": player_id,
            "season": season,
            "stat": stat_name,
            **consistencia
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular consistência: {str(e)}")

@router.get("/dashboard")
def get_betting_dashboard(season: int = Query(), stat_name: str = Query(), db: Session = Depends(get_db)):
    try:
        over_under = identificar_oportunidades_over_under(db=db, season=season, stat_name=stat_name, min_games=10, threshold_percentage=15.0, limit=5)        
        high_confidence = identificar_high_confidence_bets(db=db, season=season, stat_name=stat_name, max_cv=30.0, min_games=15, limit=5)
        
        return {
            "season": season,
            "stat": stat_name,
            "summary": {
                "total_over_under_opportunities": len(over_under),
                "total_high_confidence_bets": len(high_confidence),
                "best_edge": over_under[0]["edge"] if over_under else 0,
                "most_consistent_player": high_confidence[0]["player_name"] if high_confidence else None
            },
            "top_over_under_opportunities": over_under,
            "top_high_confidence_bets": high_confidence
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar dashboard: {str(e)}")