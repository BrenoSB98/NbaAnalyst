import os
import sys
import logging

sys.path.insert(0, os.environ.get("AIRFLOW_BACKEND_PATH", "/opt/airflow/backend"))

from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.operators.python import get_current_context
from app.config import config

logger = logging.getLogger("nba_playoffs_dag")

TEMPORADA_ATUAL = config.NBA_SEASON
LIGA_STANDARD = "standard"
DIAS_ANTECIPACAO = 3

args_padrao = {
    "owner": "nba_score",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
    "email_on_failure": False,
    "email_on_retry": False,
}


@dag(
    dag_id="nba_carga_playoffs",
    default_args=args_padrao,
    description="Carrega jogos dos proximos dias para garantir que partidas de playoffs apareçam antes de ocorrerem",
    schedule_interval="0 11 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["nba", "playoffs"],
)
def nba_carga_playoffs():

    @task()
    def carregar_jogos_proximos_dias():
        from app.etl.carregar_partidas import carregar_partidas

        contexto = get_current_context()
        data_execucao = datetime.strptime(contexto["ds"], "%Y-%m-%d")

        total_carregados = 0
        total_erros = 0

        for delta in range(0, DIAS_ANTECIPACAO + 1):
            data_alvo = data_execucao + timedelta(days=delta)
            data_str = data_alvo.strftime("%Y-%m-%d")

            try:
                logger.warning(f"Carregando jogos futuros: temporada={TEMPORADA_ATUAL}, data={data_str}")
                carregar_partidas(season=TEMPORADA_ATUAL, date=data_str, league_id=LIGA_STANDARD)
                total_carregados = total_carregados + 1
                logger.warning(f"Jogos carregados: data={data_str}")
            except Exception as erro:
                total_erros = total_erros + 1
                logger.warning(f"Erro ao carregar jogos: data={data_str}: {erro}")

        logger.warning(f"Carga de playoffs concluida: datas_ok={total_carregados}, erros={total_erros}, temporada={TEMPORADA_ATUAL}")

    carregar_jogos_proximos_dias()

dag_instance = nba_carga_playoffs()