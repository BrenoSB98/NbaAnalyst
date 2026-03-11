from fastapi import Query

from app.config import config
from app.db.db_utils import get_db  # noqa: F401

STATS_PERMITIDAS = ["points", "assists", "tot_reb", "steals", "blocks", "turnovers"]

class ParametrosPaginacao:
    def __init__(
        self,
        pagina: int = Query(default=1, ge=1, description="Número da página (começa em 1)"),
        tamanho: int = Query(default=20, ge=1, le=100, description="Quantidade de itens por página"),
    ):
        self.pagina = pagina
        self.tamanho = tamanho
        self.offset = (pagina - 1) * tamanho
        self.limite = tamanho

def obter_temporada(temporada: int = Query(default=None, description="Temporada NBA. Se não informada, usa a temporada atual.")):
    if temporada:
        return temporada
    return config.NBA_SEASON