import os
import sys
import logging

sys.path.insert(0, os.environ.get("AIRFLOW_BACKEND_PATH", "/opt/airflow/backend"))

from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.operators.python import get_current_context

from app.config import config
from app.db.db_utils import get_db
from app.db.models import Game
from app.etl.carregar_partidas import carregar_partidas
from app.etl.carregar_stats_jogadores import carregar_stats_jogador, carregar_stats_todos_jogadores
from app.etl.carregar_stats_times import carregar_stats_times_jogo, carregar_stats_todos_times

logger = logging.getLogger("nba_daily_incremental_dag")
TEMPORADA_ATUAL = config.NBA_SEASON

args_padrao = {
    "owner": "nba_score",
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
    "email_on_retry": False,
}

@dag(
    dag_id="nba_carga_diaria_incremental",
    default_args=args_padrao,
    description="Carga diária NBA",
    schedule_interval="0 8 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["nba", "incremental"],
)
def nba_carga_diaria_incremental():
    @task()
    def carregar_partidas_do_dia():
        contexto = get_current_context()
        data_execucao = contexto["ds"]
        carregar_partidas(season=TEMPORADA_ATUAL, date=data_execucao)

    @task()
    def carregar_stats_jogadores_do_dia():
        contexto = get_current_context()
        data_execucao = contexto["ds"]
        carregar_stats_todos_jogadores(season=TEMPORADA_ATUAL, data=data_execucao)
        
    @task()
    def carregar_stats_times_do_dia():
        contexto = get_current_context()
        data_execucao = contexto["ds"]
        carregar_stats_todos_times(season=TEMPORADA_ATUAL, data=data_execucao)

    op_partidas = carregar_partidas_do_dia()
    op_stats_jogadores = carregar_stats_jogadores_do_dia()
    op_stats_times = carregar_stats_times_do_dia()

    op_partidas >> op_stats_jogadores >> op_stats_times

dag_instance = nba_carga_diaria_incremental()
