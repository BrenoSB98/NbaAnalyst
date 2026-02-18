import logging
from typing import Any, Dict

from app.services import nba_api_client
from app.db.models import League
from app.db.db_utils import get_db

from app.etl.func_normalize import _normalizar_string

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _processar_item_liga(item: Any) -> Dict[str, str | None]:
    """
    Processa um item de liga da API, extraindo código e nome.
    """
    if isinstance(item, dict):
        code = item.get("code") or item.get("id") or item.get("name")
        name = item.get("name") or item.get("code") or item.get("id")
        return {
            "code": _normalizar_string(str(code) if code is not None else None),
            "name": _normalizar_string(str(name) if name is not None else None),
        }
    if isinstance(item, str):
        valor_normalizado = _normalizar_string(item)
        return {"code": valor_normalizado, "name": valor_normalizado}

    logger.warning(f"Tipo inesperado de item de liga: {item!r}")
    return {"code": None, "name": None}


def carregar_ligas():
    """
    Carrega ligas da NBA a partir da API e insere no banco de dados.
    """
    logger.info("Iniciando carga de ligas NBA...")

    dados_ligas = nba_api_client.get_leagues()
    if not dados_ligas:
        logger.warning("Sem ligas para carregar.")
        return

    ligas_carregadas = 0
    ligas_existentes = 0
    ligas_incompletas = 0
    for db in get_db():
        for item in dados_ligas:
            dados_processados = _processar_item_liga(item)
            codigo_liga = dados_processados["code"]
            nome_liga = dados_processados["name"]

            if not codigo_liga or not nome_liga:
                logger.warning(f"Dado de liga incompleto: {item}. Pulando...")
                ligas_incompletas += 1
                continue

            liga_existente = db.query(League).filter(League.code == codigo_liga).first()
            if liga_existente:
                ligas_existentes += 1
                continue

            nova_liga = League(code=codigo_liga, description=nome_liga)
            db.add(nova_liga)
            ligas_carregadas += 1

    logger.info(
        f"Carga de ligas NBA concluída. "
        f"{ligas_carregadas} carregadas, {ligas_existentes} já existiam, "
        f"{ligas_incompletas} incompletas."
    )

if __name__ == "__main__":
    carregar_ligas()