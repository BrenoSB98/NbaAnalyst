import os
import sys
import logging

sys.path.insert(0, os.environ.get("AIRFLOW_BACKEND_PATH", "/opt/airflow/backend"))

from datetime import datetime, timedelta

from airflow.decorators import dag, task

from app.config import config

logger = logging.getLogger("nba_retreinamento_semanal_dag")

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
    dag_id="nba_retreinamento_semanal",
    default_args=args_padrao,
    description="Retreina os modelos preditivos com os dados mais recentes da temporada",
    schedule_interval="0 7 * * 1",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["nba", "ml", "retreinamento"],
)
def nba_retreinamento_semanal():

    @task()
    def retreinar_modelos():
        from app.db.db_utils import get_db
        from app.services.modelo_service import retreinar_todos_modelos

        logger.warning(f"Iniciando retreinamento semanal —> temporada={TEMPORADA_ATUAL}")
        total_salvos = 0
        try:
            for db in get_db():
                total_salvos = retreinar_todos_modelos(db=db, season=TEMPORADA_ATUAL)
        except Exception as erro:
            logger.warning(f"Falha no retreinamento semanal —> temporada={TEMPORADA_ATUAL}: {erro}")
            raise

        logger.warning(f"Retreinamento semanal concluido —> modelos_salvos={total_salvos}, temporada={TEMPORADA_ATUAL}")
    retreinar_modelos()

dag_instance = nba_retreinamento_semanal()