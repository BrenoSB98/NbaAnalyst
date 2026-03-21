import os
import sys
import logging

sys.path.insert(0, os.environ.get("AIRFLOW_BACKEND_PATH", "/opt/airflow/backend"))

from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.models.param import Param
from airflow.operators.python import get_current_context

from app.config import config
from app.etl.carregar_ligas import carregar_ligas
from app.etl.carregar_temporadas import carregar_temporadas
from app.etl.carregar_franquias import carregar_times
from app.etl.carregar_jogadores_franquias import carregar_jogadores_franquias
from app.etl.carregar_partidas import carregar_partidas
from app.etl.carregar_stats_jogadores import carregar_stats_todos_jogadores
from app.etl.carregar_stats_times import carregar_stats_todos_times

logger = logging.getLogger("nba_backfill_historico_dag")

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
    description="Carga histórica de dados NBA — range de temporadas configurável",
    schedule_interval=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["nba", "backfill"],
    params={
        "temporada_inicio": Param(
            default=2021,
            type="integer",
            description="Primeira temporada a carregar (ex: 2021)",
            minimum=2015,
            maximum=2025,
        ),
        "temporada_fim": Param(
            default=2025,
            type="integer",
            description="Última temporada a carregar (ex: 2025)",
            minimum=2015,
            maximum=2025,
        ),
        "carregar_ligas_times": Param(
            default=True,
            type="boolean",
            description="Carregar ligas e times (só necessário na primeira execução)",
        ),
        "carregar_jogadores": Param(
            default=True,
            type="boolean",
            description="Carregar elencos por temporada",
        ),
    },
)
def nba_backfill_historico():
    @task()
    def obter_temporadas():
        contexto = get_current_context()
        params = contexto["params"]

        inicio = int(params["temporada_inicio"])
        fim    = int(params["temporada_fim"])

        if inicio > fim:
            raise ValueError(f"temporada_inicio ({inicio}) não pode ser maior que temporada_fim ({fim}).")

        temporadas = list(range(inicio, fim + 1))
        logger.warning(f"Backfill configurado para temporadas: {temporadas}")
        return temporadas

    @task()
    def carregar_ligas_task(temporadas):
        contexto = get_current_context()
        if not contexto["params"]["carregar_ligas_times"]:
            logger.warning("Pulando carga de ligas (desabilitado nos parâmetros).")
            return
        logger.warning("Carregando ligas...")
        carregar_ligas()
        logger.warning("Ligas carregadas.")

    @task()
    def carregar_temporadas_task(temporadas):
        logger.warning("Carregando temporadas...")
        carregar_temporadas()
        logger.warning("Temporadas carregadas.")

    @task()
    def carregar_times_task(temporadas):
        contexto = get_current_context()
        if not contexto["params"]["carregar_ligas_times"]:
            logger.warning("Pulando carga de times (desabilitado nos parâmetros).")
            return
        logger.warning("Carregando franquias...")
        carregar_times()
        logger.warning("Franquias carregadas.")

    @task()
    def carregar_jogadores_task(temporadas):
        contexto = get_current_context()
        if not contexto["params"]["carregar_jogadores"]:
            logger.warning("Pulando carga de jogadores (desabilitado nos parâmetros).")
            return

        for temporada in temporadas:
            logger.warning(f"Carregando elencos —> temporada={temporada}")
            try:
                carregar_jogadores_franquias(temporada=temporada)
                logger.warning(f"Elencos carregados —> temporada={temporada}")
            except Exception as erro:
                logger.error(f"Erro ao carregar elencos —> temporada={temporada}: {erro}")
                continue

    @task()
    def carregar_partidas_task(temporadas):
        for temporada in temporadas:
            logger.warning(f"Carregando partidas —> temporada={temporada}")
            try:
                carregar_partidas(season=temporada)
                logger.warning(f"Partidas carregadas —> temporada={temporada}")
            except Exception as erro:
                logger.error(f"Erro ao carregar partidas —> temporada={temporada}: {erro}")
                continue

    @task()
    def carregar_stats_jogadores_task(temporadas):
        for temporada in temporadas:
            logger.warning(f"Carregando stats de jogadores —> temporada={temporada}")
            try:
                carregar_stats_todos_jogadores(season=temporada)
                logger.warning(f"Stats de jogadores carregados —> temporada={temporada}")
            except Exception as erro:
                logger.error(f"Erro ao carregar stats de jogadores —> temporada={temporada}: {erro}")
                continue

    @task()
    def carregar_stats_times_task(temporadas):
        for temporada in temporadas:
            logger.warning(f"Carregando stats de times —> temporada={temporada}")
            try:
                carregar_stats_todos_times(season=temporada)
                logger.warning(f"Stats de times carregados —> temporada={temporada}")
            except Exception as erro:
                logger.error(f"Erro ao carregar stats de times —> temporada={temporada}: {erro}")
                continue

    temporadas = obter_temporadas()

    op_ligas        = carregar_ligas_task(temporadas)
    op_temporadas   = carregar_temporadas_task(temporadas)
    op_times        = carregar_times_task(temporadas)
    op_jogadores    = carregar_jogadores_task(temporadas)
    op_partidas     = carregar_partidas_task(temporadas)
    op_stats_jog    = carregar_stats_jogadores_task(temporadas)
    op_stats_times  = carregar_stats_times_task(temporadas)

    temporadas >> op_ligas >> op_temporadas >> op_times >> op_jogadores >> op_partidas >> op_stats_jog >> op_stats_times

dag_instance = nba_backfill_historico()