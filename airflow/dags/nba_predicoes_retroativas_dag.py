import logging
import os
import sys

sys.path.insert(0, os.environ.get("AIRFLOW_BACKEND_PATH", "/opt/airflow/backend"))

from datetime import datetime, timedelta

from airflow.decorators import dag, task  # type: ignore
from airflow.models.param import Param  # type: ignore
from app.config import config  # type: ignore

logger = logging.getLogger("nba_predicoes_retroativas_dag")
TEMPORADA_ATUAL = config.NBA_SEASON

args_padrao = {
    "owner": "nba_score",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
    "email_on_failure": False,
    "email_on_retry": False,
}


@dag(
    dag_id="nba_predicoes_retroativas",
    default_args=args_padrao,
    description="Deleta as predicoes de uma temporada e regera retroativamente usando data_corte por jogo",
    schedule_interval=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["nba", "predicoes", "retroativo"],
    params={
        "temporada": Param(
            TEMPORADA_ATUAL,
            type="integer",
            title="Temporada",
            description="Temporada para gerar as predicoes retroativas (ex: 2025, 2024, 2023). Padrao: temporada atual.",
        ),
    },
)
def nba_predicoes_retroativas():
    @task()
    def deletar_predicoes(**context):
        from app.db.db_utils import get_db  # type: ignore
        from app.services.manager_service import deletar_todas_predicoes  # type: ignore

        temporada = int(context["params"]["temporada"])
        logger.info(f"Deletando todas as predicoes: temporada={temporada}")
        total = 0
        for db in get_db():
            total = deletar_todas_predicoes(db=db, season=temporada)
        logger.info(f"Predicoes deletadas: total={total}, temporada={temporada}")

    @task()
    def gerar_retroativo(**context):
        from app.db.db_utils import get_db  # type: ignore
        from app.services.manager_service import (  # type: ignore
            gerar_predicoes_retroativas,  # type: ignore
        )

        temporada = int(context["params"]["temporada"])
        if temporada != TEMPORADA_ATUAL:
            logger.warning(
                f"Gerando retroativo para temporada anterior: temporada={temporada}, temporada_atual={TEMPORADA_ATUAL}. Os modelos atuais foram treinados com dados de outras temporadas, entao o resultado serve para validacao, nao reflete um cenario sem vazamento temporal."
            )
        logger.info(f"Gerando predicoes retroativas: temporada={temporada}")
        total = 0
        for db in get_db():
            total = gerar_predicoes_retroativas(db=db, season=temporada)
        logger.info(
            f"Predicoes retroativas concluidas: total={total}, temporada={temporada}"
        )

    op_deletar = deletar_predicoes()
    op_gerar = gerar_retroativo()

    op_deletar >> op_gerar  # type: ignore


dag_instance = nba_predicoes_retroativas()
