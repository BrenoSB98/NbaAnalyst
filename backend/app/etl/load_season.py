import logging

from app.services import nba_api_client
from app.db.models import Season
from app.db.db_utils import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_season():
    logger.info("Iniciando carga de temporada NBA...")
    
    season_data = nba_api_client.get_seasons()
    if not season_data:
        logger.error("Sem temporadas para carregar.")
        return
    with get_db() as db:
        for year in season_data:
            query_season = db.query(Season).filter(Season.season == year).first()
            
            if query_season:
                logger.info(f"Temporada {year} já existe. Pulando...")
                continue
            new_season = Season(season=year)
            db.add(new_season)
            logger.info(f"Temporada {year} carregada com sucesso.")    
    logger.info("Carga de temporada NBA concluída.")

if __name__ == "__main__":
    load_season()