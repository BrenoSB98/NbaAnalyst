import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import obter_temporada
from app.db.db_utils import get_db
from app.schemas.win_rate import WinRateResponse
from app.services.win_rate_service import calcular_win_rate

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/desempenho", response_model=WinRateResponse)
def get_win_rate(temporada_alvo: int = Depends(obter_temporada), db: Session = Depends(get_db)):
    resultado = calcular_win_rate(db, temporada_alvo)

    if not resultado:
        logger.warning(f"Sem dados de win rate —> temporada={temporada_alvo}")
        raise HTTPException(status_code=404, detail=f"Nenhum palpite avaliavel encontrada para a temporada {temporada_alvo}.")
    return resultado