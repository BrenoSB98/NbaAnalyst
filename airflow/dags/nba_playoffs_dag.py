import os
import sys
import logging

sys.path.insert(0, os.environ.get("AIRFLOW_BACKEND_PATH", "/opt/airflow/backend"))

from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.operators.python import get_current_context

from app.config import config
from app.etl.carregar_partidas import carregar_partidas

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
    description="Carrega jogos de playoffs dos próximos dias para manter o calendário atualizado",
    schedule_interval="0 11 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["nba", "playoffs"],
)
def nba_carga_playoffs():
    @task()
    def carregar_jogos_proximos_dias():
        contexto = get_current_context()
        data_execucao = datetime.strptime(contexto["ds"], "%Y-%m-%d")

        total_carregados = 0

        for delta in range(0, DIAS_ANTECIPACAO + 1):
            data_alvo = data_execucao + timedelta(days=delta)
            data_str = data_alvo.strftime("%Y-%m-%d")

            logger.warning(f"Buscando jogos futuros —> temporada={TEMPORADA_ATUAL}, data={data_str}")
            try:
                carregar_partidas(season=TEMPORADA_ATUAL, date=data_str, league_id=LIGA_STANDARD)
                total_carregados = total_carregados + 1
                logger.warning(f"Jogos futuros carregados —> data={data_str}")
            except Exception as erro:
                logger.warning(f"Erro ao carregar jogos futuros —> data={data_str}: {erro}")

        logger.warning(f"Carga de playoffs concluida —> {total_carregados} datas processadas, temporada={TEMPORADA_ATUAL}")

    carregar_jogos_proximos_dias()

dag_instance = nba_carga_playoffs()