import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.db_utils import get_db
from app.db.models import League
from app.schemas.league import LigasResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=LigasResponse)
def listar_ligas(db: Session = Depends(get_db)):
    ligas = db.query(League).all()

    lista_ligas = []
    for liga in ligas:
        lista_ligas.append({
            "id": liga.id, 
            "code": liga.code, 
            "descricao": liga.description
            })

    return {
        "total": len(lista_ligas), 
        "ligas": lista_ligas
        }