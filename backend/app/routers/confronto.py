import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.db_utils import get_db
from app.services.confronto_service import analisar_confronto
from app.routers.auth import obter_usuario_atual

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/analise")
def get_analise_confronto(time_casa_id: int = Query(...), time_fora_id: int = Query(...), ultimos_n: int = Query(5, ge=1, le=20), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    if time_casa_id == time_fora_id:
        raise HTTPException(status_code=400, detail="Os dois times devem ser diferentes.")

    resultado = analisar_confronto(db=db, time_casa_id=time_casa_id, time_fora_id=time_fora_id, ultimos_n=ultimos_n)
    if not resultado:
        logger.warning(f"Confronto sem resultado —> time_casa_id={time_casa_id}, time_fora_id={time_fora_id}")
        raise HTTPException(status_code=404, detail="Um ou mais times não foram encontrados ou não há dados disponíveis.")
    return resultado