import logging

from app.db.models import Team
from app.db.db_utils import get_db
from app.etl.load_players import load_players

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_team_players(season: int):
    logger.info(f"Iniciando carga de jogadores para a temporada {season}...")
    
    with get_db() as db:
        team_ids = db.query(Team).all()
        
        if not team_ids:
            logger.error("Sem times encontrados para carregar jogadores.")
            return
        
        for team in team_ids:
            load_players(team_id=team.id, season=season)
            
    logger.info(f"Carga de jogadores para a temporada {season} concluída.")
    
if __name__ == "__main__":
    load_team_players()