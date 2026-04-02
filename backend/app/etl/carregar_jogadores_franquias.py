from app.db.models import Team
from app.db.db_utils import get_db
from app.etl.carregar_jogadores import carregar_jogadores
from app.core.logging_config import configurar_logger

logger = configurar_logger(__name__)

def carregar_jogadores_franquias(temporada):
    logger.info(f"Iniciando carga de jogadores — temp={temporada}.")

    for db in get_db():
        times = db.query(Team).filter(Team.nba_franchise == True).all()

        if not times:
            logger.warning("Nenhum time NBA no banco.")
            return

        logger.info(f"{len(times)} times encontrados.")
        total_erros = 0

        for time in times:
            logger.info(f"Carregando {time.name}...")
            try:
                carregar_jogadores(team_id=time.id, season=temporada)
            except Exception as erro:
                total_erros += 1
                logger.warning(f"Erro em {time.name}: {erro}")
                continue

        if total_erros > 0:
            logger.warning(f"Fim com erros — erros={total_erros}.")
        else:
            logger.info("Fim sem erros.")

if __name__ == "__main__":
    carregar_jogadores_franquias(temporada=2025)