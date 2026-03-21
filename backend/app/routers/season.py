import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.db_utils import get_db
from app.db.models import Season
from app.schemas.season import TemporadasResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("", response_model=TemporadasResponse)
def listar_temporadas(db: Session = Depends(get_db)):
    temporadas = db.query(Season).order_by(Season.season.desc()).all()

    lista_temporadas = []
    for temporada in temporadas:
        lista_temporadas.append({"season": temporada.season})

    return {"total": len(lista_temporadas), 
            "temporadas": lista_temporadas
            }