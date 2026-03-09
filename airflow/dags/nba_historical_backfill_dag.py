import os
import sys
import logging

sys.path.insert(0, os.environ.get("AIRFLOW_BACKEND_PATH", "/opt/airflow/backend"))

from datetime import datetime, timedelta

from airflow.decorators import dag, task

from app.config import config
from app.etl.carregar_ligas import carregar_ligas
from app.etl.carregar_temporadas import carregar_temporadas
from app.etl.carregar_franquias import carregar_times
from app.etl.carregar_jogadores_franquias import carregar_jogadores_franquias
from app.etl.carregar_partidas import carregar_partidas
from app.etl.carregar_stats_jogadores import carregar_stats_todos_jogadores
from app.etl.carregar_stats_times import carregar_stats_todos_times

logger = logging.getLogger("nba_backfill_historico_dag")
TEMPORADAS_HISTORICAS = list(range(2015, config.NBA_SEASON + 1))

args_padrao = {
    "owner": "nba_score",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
    "email_on_failure": False,
    "email_on_retry": False,
}

@dag(
    dag_id="nba_backfill_historico",
    default_args=args_padrao,
    description="Carga histórica completa de dados NBA — execução única",
    schedule_interval=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["nba", "backfill"],
)
def nba_backfill_historico():
    @task()
    def carregar_ligas_task():
        carregar_ligas()

    @task()
    def carregar_temporadas_task():
        carregar_temporadas()

    @task()
    def carregar_times_task():
        carregar_times()

    @task()
    def carregar_jogadores_task():
        for temporada in TEMPORADAS_HISTORICAS:
            try:
                carregar_jogadores_franquias(season=temporada)
            except Exception as erro:
                logger.error(f"Erro ao carregar jogadores da temporada {temporada}: {erro}")
                continue

    @task()
    def carregar_partidas_task():
        for temporada in TEMPORADAS_HISTORICAS:
            try:
                carregar_partidas(season=temporada)
            except Exception as erro:
                logger.error(f"Erro ao carregar partidas da temporada {temporada}: {erro}")
                continue

    @task()
    def carregar_stats_jogadores_task():
        for temporada in TEMPORADAS_HISTORICAS:
            try:
                carregar_stats_todos_jogadores(season=temporada)
            except Exception as erro:
                logger.error(f"Erro ao carregar stats de jogadores da temporada {temporada}: {erro}")
                continue

    @task()
    def carregar_stats_times_task():
        for temporada in TEMPORADAS_HISTORICAS:
            try:
                carregar_stats_todos_times(season=temporada)
            except Exception as erro:
                logger.error(f"Erro ao carregar stats de times da temporada {temporada}: {erro}")
                continue

    op_ligas = carregar_ligas_task()
    op_temporadas = carregar_temporadas_task()
    op_times = carregar_times_task()
    op_jogadores = carregar_jogadores_task()
    op_partidas = carregar_partidas_task()
    op_stats_jogadores = carregar_stats_jogadores_task()
    op_stats_times = carregar_stats_times_task()

    op_ligas >> op_temporadas >> op_times >> op_jogadores >> op_partidas >> op_stats_jogadores >> op_stats_times

dag_instance = nba_backfill_historico()