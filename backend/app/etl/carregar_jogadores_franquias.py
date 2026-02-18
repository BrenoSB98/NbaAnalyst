import logging

from app.db.models import Team
from app.db.db_utils import get_db
from app.etl.carregar_jogadores import carregar_jogadores

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def carregar_jogadores_franquias(season: int):
    """
    Carrega jogadores de todos os times da NBA para uma temporada específica.
    """
    logger.info(f"Iniciando carga de jogadores para a temporada {season}...")

    for db in get_db():
        times = db.query(Team).filter(Team.nba_franchise == True).all()

        if not times:
            logger.error("Nenhum time NBA encontrado no banco de dados.")
            return

        total_times = len(times)
        times_processados = 0
        times_com_erro = 0

        for time in times:
            try:                
                carregar_jogadores(team_id=time.id, season=season)
                times_processados += 1
            except Exception as erro:
                logger.error(f"Erro ao carregar jogadores do time {time.name} (ID: {time.id}): {erro}")
                times_com_erro += 1
                continue

    logger.info(
        f"Carga de jogadores para todas as franquias concluída. "
        f"{times_processados} times processados, {times_com_erro} com erro."
    )

if __name__ == "__main__":
    carregar_jogadores_franquias(season=2023)