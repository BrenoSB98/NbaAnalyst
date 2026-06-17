import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.db_utils import get_db
from app.schemas.win_rate import WinRateResponse
from app.services.win_rate_service import calcular_win_rate

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/desempenho", response_model=WinRateResponse)
def get_win_rate(
    temporada: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    resultado = calcular_win_rate(db, temporada)

    if not resultado:
        logger.warning(f"Sem dados de win rate, temporada={temporada}")
        raise HTTPException(
            status_code=404, detail="Nenhum palpite avaliavel encontrado."
        )
    return resultado
