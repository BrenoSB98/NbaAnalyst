from fastapi import APIRouter, HTTPException

from app.services import nba_api_client

router = APIRouter(prefix="/nba", tags=["nba"])

@router.get("/seasons")
def list_seasons():
    seasons = nba_api_client.get_seasons()
    if seasons is None:
        raise HTTPException(status_code=502, detail="Erro ao consultar temporadas na API")
    return {"seasons": seasons}