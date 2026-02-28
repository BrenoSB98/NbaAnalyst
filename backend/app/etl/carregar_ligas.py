from app.services import nba_api_client
from app.db.models import League
from app.db.db_utils import get_db
from app.etl.func_normalize import _normalizar_string

def _processar_item_liga(item):
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
    return {"code": None, "name": None}

def carregar_ligas():
    dados_ligas = nba_api_client.get_leagues()
    if not dados_ligas:
        return

    for db in get_db():
        for item in dados_ligas:
            dados_processados = _processar_item_liga(item)
            codigo_liga = dados_processados["code"]
            nome_liga = dados_processados["name"]

            if not codigo_liga or not nome_liga:
                continue

            liga_existente = db.query(League).filter(League.code == codigo_liga).first()
            if liga_existente:
                continue

            nova_liga = League(code=codigo_liga, description=nome_liga)
            db.add(nova_liga)

if __name__ == "__main__":
    carregar_ligas()