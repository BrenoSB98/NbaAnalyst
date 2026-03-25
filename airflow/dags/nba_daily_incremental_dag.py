import os
import sys
import logging

sys.path.insert(0, os.environ.get("AIRFLOW_BACKEND_PATH", "/opt/airflow/backend"))

from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.operators.python import get_current_context

from app.config import config
from app.etl.carregar_partidas import carregar_partidas
from app.etl.carregar_stats_jogadores import carregar_stats_todos_jogadores
from app.etl.carregar_stats_times import carregar_stats_todos_times
from app.etl.carregar_jogadores_franquias import carregar_jogadores_franquias
from app.services.manager_service import salvar_predicoes_dia_atual

logger = logging.getLogger("nba_daily_incremental_dag")

TEMPORADA_ATUAL = config.NBA_SEASON
LIGA_STANDARD = "standard"

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
    description="Carga diária incremental de partidas e estatísticas da NBA",
    schedule_interval="0 9 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["nba", "incremental"],
)
def nba_carga_diaria_incremental():
    @task()
    def carregar_partidas_do_dia():
        contexto = get_current_context()
        data_execucao = contexto["ds"]
        data_ontem = (datetime.strptime(data_execucao, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")

        logger.info(f"Carregando partidas —> temporada={TEMPORADA_ATUAL}, data_utc={data_ontem}")
        carregar_partidas(season=TEMPORADA_ATUAL, date=data_ontem, league_id=LIGA_STANDARD)
        logger.info(f"Partidas carregadas —> temporada={TEMPORADA_ATUAL}, data_utc={data_ontem}")

        logger.info(f"Carregando partidas (madrugada BRT) —> temporada={TEMPORADA_ATUAL}, data_utc={data_execucao}")
        carregar_partidas(season=TEMPORADA_ATUAL, date=data_execucao, league_id=LIGA_STANDARD)
        logger.info(f"Partidas carregadas (madrugada BRT) —> temporada={TEMPORADA_ATUAL}, data_utc={data_execucao}")

    @task()
    def carregar_jogadores_do_dia():
        logger.info(f"Carregando jogadores das franquias —> temporada={TEMPORADA_ATUAL}")
        carregar_jogadores_franquias(temporada=TEMPORADA_ATUAL)
        logger.info(f"Jogadores carregados —> temporada={TEMPORADA_ATUAL}")

    @task()
    def carregar_stats_jogadores_do_dia():
        contexto = get_current_context()
        data_execucao = contexto["ds"]
        data_ontem = (datetime.strptime(data_execucao, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")

        logger.info(f"Carregando stats de jogadores —> temporada={TEMPORADA_ATUAL}, data_utc={data_ontem}")
        carregar_stats_todos_jogadores(season=TEMPORADA_ATUAL, data=data_ontem)
        logger.info(f"Stats de jogadores carregadas —> temporada={TEMPORADA_ATUAL}, data_utc={data_ontem}")

        logger.info(f"Carregando stats de jogadores (madrugada BRT) —> temporada={TEMPORADA_ATUAL}, data_utc={data_execucao}")
        carregar_stats_todos_jogadores(season=TEMPORADA_ATUAL, data=data_execucao)
        logger.info(f"Stats de jogadores carregadas (madrugada BRT) —> temporada={TEMPORADA_ATUAL}, data_utc={data_execucao}")

    @task()
    def carregar_stats_times_do_dia():
        contexto = get_current_context()
        data_execucao = contexto["ds"]
        data_ontem = (datetime.strptime(data_execucao, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")

        logger.info(f"Carregando stats de times —> temporada={TEMPORADA_ATUAL}, data_utc={data_ontem}")
        carregar_stats_todos_times(season=TEMPORADA_ATUAL, data=data_ontem)
        logger.info(f"Stats de times carregadas —> temporada={TEMPORADA_ATUAL}, data_utc={data_ontem}")

        logger.info(f"Carregando stats de times (madrugada BRT) —> temporada={TEMPORADA_ATUAL}, data_utc={data_execucao}")
        carregar_stats_todos_times(season=TEMPORADA_ATUAL, data=data_execucao)
        logger.info(f"Stats de times carregadas (madrugada BRT) —> temporada={TEMPORADA_ATUAL}, data_utc={data_execucao}")

    @task()
    def gerar_predicoes_do_dia():
        from app.db.db_utils import get_db

        logger.info(f"Gerando predicoes do dia —> temporada={TEMPORADA_ATUAL}")
        total_geradas = 0
        for db in get_db():
            total_geradas = salvar_predicoes_dia_atual(db=db, season=TEMPORADA_ATUAL)
        logger.info(f"Predicoes do dia concluidas —> total={total_geradas}, temporada={TEMPORADA_ATUAL}")

    op_partidas = carregar_partidas_do_dia()
    op_jogadores = carregar_jogadores_do_dia()
    op_stats_jogadores = carregar_stats_jogadores_do_dia()
    op_stats_times = carregar_stats_times_do_dia()
    op_predicoes = gerar_predicoes_do_dia()

    op_partidas >> op_jogadores >> op_stats_jogadores >> op_stats_times >> op_predicoes

dag_instance = nba_carga_diaria_incremental()