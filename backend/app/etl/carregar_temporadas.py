from app.services import nba_api_client
from app.db.models import Season
from app.db.db_utils import get_db
from app.etl.func_normalize import _normalizar_inteiro

def carregar_temporadas():
    temporadas = nba_api_client.get_seasons()
    if not temporadas:
        return

    for db in get_db():
        for ano in temporadas:
            ano_normalizado = _normalizar_inteiro(ano)

            if ano_normalizado is None:
                continue

            consulta = db.query(Season).filter(Season.season == ano_normalizado).first()
            if consulta:
                continue

            nova_temporada = Season(season=ano_normalizado)
            db.add(nova_temporada)

if __name__ == "__main__":
    carregar_temporadas()