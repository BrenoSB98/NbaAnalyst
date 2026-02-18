import logging

from app.services import nba_api_client
from app.db.models import Season
from app.db.db_utils import get_db
from app.etl.func_normalize import _normalizar_inteiro

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def carregar_temporadas():
    """
    Carrega temporadas da NBA a partir da API e insere no banco de dados.
    """
    logger.info("Iniciando carga de temporadas NBA...")

    temporadas = nba_api_client.get_seasons()
    if not temporadas:
        logger.error("Sem temporadas para carregar.")
        return

    temporadas_carregadas = 0
    temporadas_existentes = 0
    temporadas_invalidas = 0
    
    for db in get_db():
        for ano in temporadas:
            ano_normalizado = _normalizar_inteiro(ano)

            if ano_normalizado is None:
                logger.warning(f"Valor de temporada inválido recebido: {ano}. Pulando...")
                temporadas_invalidas += 1
                continue

            consulta = db.query(Season).filter(Season.season == ano_normalizado).first()

            if consulta:
                temporadas_existentes += 1
                continue

            nova_temporada = Season(season=ano_normalizado)
            db.add(nova_temporada)
            temporadas_carregadas += 1

    logger.info(
        f"Carga de temporadas NBA concluída. "
        f"{temporadas_carregadas} carregadas, {temporadas_existentes} já existiam, "
        f"{temporadas_invalidas} inválidas."
    )

if __name__ == "__main__":
    carregar_temporadas()