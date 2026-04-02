from app.services import nba_api_client
from app.db.models import Season
from app.db.db_utils import get_db
from app.etl.func_normalize import _normalizar_inteiro
from app.core.logging_config import configurar_logger

logger = configurar_logger(__name__)

def carregar_temporadas():
    logger.info("Buscando temporadas...")
    temporadas = nba_api_client.get_seasons()

    if not temporadas:
        logger.warning("API retornou vazio.")
        return

    logger.info(f"{len(temporadas)} temporadas recebidas.")

    for db in get_db():
        total_inseridas = 0

        for ano in temporadas:
            ano_normalizado = _normalizar_inteiro(ano)

            if ano_normalizado is None:
                continue

            temporada_existente = db.query(Season).filter(Season.season == ano_normalizado).first()
            if temporada_existente:
                logger.info(f"Temporada {ano_normalizado} ja existe.")
                continue

            logger.info(f"Insere temporada {ano_normalizado}.")
            nova_temporada = Season(season=ano_normalizado)
            db.add(nova_temporada)
            total_inseridas += 1

        db.commit()
        logger.info("Commit ok.")

        if total_inseridas == 0:
            logger.warning("Nenhuma temporada nova.")
        else:
            logger.info(f"Fim — ins={total_inseridas}")

if __name__ == "__main__":
    carregar_temporadas()