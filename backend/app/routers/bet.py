import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import STATS_PERMITIDAS
from app.db.db_utils import get_db
from app.routers.auth import obter_usuario_atual
from app.services.bet_service import identificar_oportunidades_over_under, identificar_high_confidence_bets, analisar_tendencias_jogador, calcular_coeficiente_variacao

router = APIRouter()
logger = logging.getLogger(__name__)

def _validar_estatistica(estatistica):
    if estatistica not in STATS_PERMITIDAS:
        raise HTTPException(status_code=400, detail=f"Estatística inválida. Escolha uma das opções: {STATS_PERMITIDAS}")

@router.get("/over-under")
def get_oportunidades_over_under(temporada: int = Query(...), estatistica: str = Query(default="points"), minimo_jogos: int = Query(default=10, ge=1), threshold: float = Query(default=15.0, ge=0.0), limite: int = Query(default=10, ge=1, le=100), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    _validar_estatistica(estatistica)

    oportunidades = identificar_oportunidades_over_under(
        db=db,
        season=temporada,
        stat_name=estatistica,
        min_games=minimo_jogos,
        threshold_percentage=threshold,
        limit=limite,
    )

    return {
        "temporada": temporada,
        "estatistica": estatistica,
        "threshold_percentual": threshold,
        "total_oportunidades": len(oportunidades),
        "oportunidades": oportunidades,
    }

@router.get("/alta-confianca")
def get_apostas_alta_confianca(temporada: int = Query(...), estatistica: str = Query(...), max_cv: float = Query(..., ge=0.0), minimo_jogos: int = Query(..., ge=1), limite: int = Query(default=10, ge=1, le=100), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    _validar_estatistica(estatistica)
    apostas = identificar_high_confidence_bets(db=db, season=temporada, stat_name=estatistica, max_cv=max_cv, min_games=minimo_jogos, limit=limite)

    return {
        "temporada": temporada,
        "estatistica": estatistica,
        "coeficiente_variacao_maximo": max_cv,
        "total_jogadores": len(apostas),
        "apostas_alta_confianca": apostas,
    }

@router.get("/jogador/{jogador_id}/tendencia")
def get_tendencia_jogador(jogador_id: int, temporada: int = Query(...), estatistica: str = Query(...), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    _validar_estatistica(estatistica)
    tendencia = analisar_tendencias_jogador(db=db, player_id=jogador_id, season=temporada, stat_name=estatistica)

    if not tendencia:
        logger.warning(f"Dados insuficientes para análise de tendência —> estatistica={estatistica}")
        raise HTTPException(status_code=404, detail="Dados insuficientes para análise de tendência (mínimo 5 jogos).")
    return tendencia

@router.get("/jogador/{jogador_id}/consistencia")
def get_consistencia_jogador(jogador_id: int, temporada: int = Query(...), estatistica: str = Query(...), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    _validar_estatistica(estatistica)

    consistencia = calcular_coeficiente_variacao(db=db, player_id=jogador_id, season=temporada, stat_name=estatistica)

    if not consistencia:
        logger.warning(f"Dados insuficientes para calcular consistência —> estatistica={estatistica}")
        raise HTTPException(status_code=404, detail="Dados insuficientes para calcular consistência (mínimo 5 jogos).")

    return {
        "jogador_id": jogador_id,
        "temporada": temporada,
        "estatistica": estatistica,
        **consistencia,
    }

@router.get("/painel")
def get_painel_apostas(temporada: int = Query(...), estatistica: str = Query(...), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    _validar_estatistica(estatistica)

    over_under = identificar_oportunidades_over_under(db=db, season=temporada, stat_name=estatistica, min_games=10, threshold_percentage=15.0, limit=5)
    alta_confianca = identificar_high_confidence_bets(db=db, season=temporada, stat_name=estatistica, max_cv=30.0, min_games=15, limit=5)

    if over_under:
        melhor_edge = over_under[0].get("edge", 0)
    else:
        melhor_edge = 0

    if alta_confianca:
        jogador_mais_consistente = alta_confianca[0].get("player_name")
    else:
        jogador_mais_consistente = None

    return {
        "temporada": temporada,
        "estatistica": estatistica,
        "resumo": {
            "total_oportunidades_over_under": len(over_under),
            "total_apostas_alta_confianca": len(alta_confianca),
            "melhor_edge": melhor_edge,
            "jogador_mais_consistente": jogador_mais_consistente,
        },
        "top_oportunidades_over_under": over_under,
        "top_apostas_alta_confianca": alta_confianca,
    }