import logging

from app.services import nba_api_client
from app.db.models import Season
from app.db.db_utils import get_db
from app.etl.func_normalize import _normalizar_inteiro

logger = logging.getLogger(__name__)

def carregar_temporadas():
    temporadas = nba_api_client.get_seasons()

    if not temporadas:
        logger.warning("Nenhuma temporada retornada pela API.")
        return

    for db in get_db():
        total_inseridas = 0
        for ano in temporadas:
            ano_normalizado = _normalizar_inteiro(ano)

            if ano_normalizado is None:
                continue

            temporada_existente = db.query(Season).filter(Season.season == ano_normalizado).first()
            if temporada_existente:
                continue

            nova_temporada = Season(season=ano_normalizado)
            db.add(nova_temporada)
            total_inseridas += 1

        if total_inseridas == 0:
            logger.warning("Nenhuma temporada nova inserida, todas já existem no banco.")

if __name__ == "__main__":
    carregar_temporadas()