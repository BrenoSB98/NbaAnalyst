from fastapi import Query

from app.config import config


def obter_temporada(
    temporada: int = Query(
        default=None,
        description="Temporada NBA. Se não informada, usa a temporada atual.",
    ),
):
    if temporada:
        return temporada
    return config.NBA_SEASON
