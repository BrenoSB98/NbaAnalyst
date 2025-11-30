import logging
from typing import Any, Dict, List

from app.services import nba_api_client
from app.db.models import League
from app.db.db_utils import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _parse_league_item(item: Any) -> Dict[str, str | None]:
    if isinstance(item, dict):
        code = item.get("code") or item.get("id") or item.get("name")
        name = item.get("name") or item.get("code") or item.get("id")
        return {"code": str(code) if code is not None else None,
                "name": str(name) if name is not None else None}
    if isinstance(item, str):
        return {"code": item, "name": item}
    logger.warning("Tipo inesperado de item de liga: %r", item)
    return {"code": None, "name": None}

def load_league():
    logger.info("Iniciando carga de ligas NBA...")
    
    league_data = nba_api_client.get_leagues()
    if not league_data:
        logger.warning("Sem ligas para carregar.")
        return
    
    with get_db() as db:
        for item in league_data:
            parsed = _parse_league_item(item)
            league_id = parsed["code"]
            league_name = parsed["name"]
        
            if not league_id or not league_name:
                logger.warning(f"Dado de liga incompleto: {item}. Pulando...")
                continue
            
            query_league = db.query(League).filter(League.code == league_id).first()
            if query_league:
                logger.info(f"Liga {league_name} ({league_id}) já existe. Pulando...")
                continue
            add_league = League(code=league_id, description=league_name)
            db.add(add_league)
            logger.info(f"Liga {league_name} ({league_id}) carregada com sucesso.")    
    logger.info("Carga de ligas NBA concluída.")

if __name__ == "__main__":
    load_league()