import os
import sys
import logging

sys.path.insert(0, os.environ.get("AIRFLOW_BACKEND_PATH", "/opt/airflow/backend"))

from datetime import datetime, timedelta
from airflow.decorators import dag, task
from app.config import config

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
    description="Deleta todas as predicoes e regera retroativamente usando data_corte por jogo",
    schedule_interval=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["nba", "predicoes", "retroativo"],
)
def nba_predicoes_retroativas():
    @task()
    def deletar_predicoes():
        from app.db.db_utils import get_db
        from app.services.manager_service import deletar_todas_predicoes

        logger.warning(f"Deletando todas as predicoes: temporada={TEMPORADA_ATUAL}")
        total = 0
        for db in get_db():
            total = deletar_todas_predicoes(db=db, season=TEMPORADA_ATUAL)
        logger.warning(f"Predicoes deletadas: total={total}, temporada={TEMPORADA_ATUAL}")

    @task()
    def gerar_retroativo():
        from app.db.db_utils import get_db
        from app.services.manager_service import gerar_predicoes_retroativas

        logger.warning(f"Gerando predicoes retroativas: temporada={TEMPORADA_ATUAL}")
        total = 0
        for db in get_db():
            total = gerar_predicoes_retroativas(db=db, season=TEMPORADA_ATUAL)
        logger.warning(f"Predicoes retroativas concluidas: total={total}, temporada={TEMPORADA_ATUAL}")

    op_deletar = deletar_predicoes()
    op_gerar = gerar_retroativo()

    op_deletar >> op_gerar

dag_instance = nba_predicoes_retroativas()