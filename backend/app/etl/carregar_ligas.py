import logging

from app.services import nba_api_client
from app.db.models import League
from app.db.db_utils import get_db
from app.etl.func_normalize import _normalizar_string

logger = logging.getLogger(__name__)

def _extrair_dados_liga(item):
    if isinstance(item, dict):
        codigo = item.get("code") or item.get("id") or item.get("name")
        nome = item.get("name") or item.get("code") or item.get("id")

        codigo_normalizado = _normalizar_string(str(codigo) if codigo is not None else None)
        nome_normalizado = _normalizar_string(str(nome) if nome is not None else None)
        return {"codigo": codigo_normalizado, "nome": nome_normalizado}

    if isinstance(item, str):
        valor = _normalizar_string(item)
        return {"codigo": valor, "nome": valor}
    return {"codigo": None, "nome": None}

def carregar_ligas():
    dados_ligas = nba_api_client.get_leagues()
    if not dados_ligas:
        logger.warning("Nenhuma liga retornada pela API.")
        return

    for db in get_db():
        total_inseridas = 0
        total_atualizadas = 0
        for item in dados_ligas:
            dados = _extrair_dados_liga(item)
            codigo_liga = dados["codigo"]
            nome_liga = dados["nome"]

            if not codigo_liga or not nome_liga:
                continue

            liga_existente = db.query(League).filter(League.code == codigo_liga).first()
            if liga_existente:
                if liga_existente.description != nome_liga:
                    liga_existente.description = nome_liga
                    total_atualizadas = total_atualizadas + 1
                continue

            nova_liga = League(code=codigo_liga, description=nome_liga)
            db.add(nova_liga)
            total_inseridas += 1

        if total_inseridas == 0 and total_atualizadas == 0:
            logger.warning("Nenhuma liga nova inserida ou atualizada. Todos os registros já existem no banco.")

if __name__ == "__main__":
    carregar_ligas()