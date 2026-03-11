import logging

from app.db.models import Team
from app.db.db_utils import get_db
from app.etl.carregar_jogadores import carregar_jogadores

logger = logging.getLogger(__name__)

def carregar_jogadores_franquias(temporada):
    for db in get_db():
        times = db.query(Team).filter(Team.nba_franchise == True).all()

        if not times:
            logger.warning("Nenhum time NBA encontrado no banco.")
            return

        total_erros = 0
        for time in times:
            try:
                carregar_jogadores(team_id=time.id, season=temporada)
            except Exception as erro:
                total_erros += 1
                logger.warning(f"Erro ao carregar jogadores da franquia {time.name} na temporada={temporada}: {erro}")
                continue

        if total_erros > 0:
            logger.warning(f"Carga concluída com erros")

if __name__ == "__main__":
    carregar_jogadores_franquias(temporada=2025)