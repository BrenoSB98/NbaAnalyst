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
from app.etl.carregar_stats_jogadores import carregar_stats_todos_jogadores, carregar_stats_jogador
from app.etl.carregar_stats_times import carregar_stats_todos_times, carregar_stats_times_jogo
from app.services.manager_service import salvar_predicoes_temporada

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
        params   = contexto["params"]

        inicio = int(params["temporada_inicio"])
        fim    = int(params["temporada_fim"])

        if inicio > fim:
            raise ValueError(f"temporada_inicio ({inicio}) nao pode ser maior que temporada_fim ({fim}).")

        temporadas = list(range(inicio, fim + 1))
        logger.warning(f"Backfill configurado para temporadas: {temporadas}")
        return temporadas

    @task()
    def carregar_ligas_task(temporadas):
        contexto = get_current_context()
        if not contexto["params"]["carregar_ligas_times"]:
            logger.warning("Pulando carga de ligas (desabilitado nos parametros).")
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
            logger.warning("Pulando carga de times (desabilitado nos parametros).")
            return
        logger.warning("Carregando franquias...")
        carregar_times()
        logger.warning("Franquias carregadas.")

    @task()
    def carregar_jogadores_task(temporadas):
        contexto = get_current_context()
        if not contexto["params"]["carregar_jogadores"]:
            logger.warning("Pulando carga de jogadores (desabilitado nos parametros).")
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

    @task()
    def reprocessar_stats_pendentes_task(temporadas):
        from app.db.db_utils import get_db
        from app.db.models import Game, GameTeamStats, PlayerGameStats

        for db in get_db():
            for temporada in temporadas:
                jogos_finalizados = db.query(Game).filter(Game.season == temporada, Game.status_short == 3).all()

                ids_sem_stats_times     = []
                ids_sem_stats_jogadores = []
                for jogo in jogos_finalizados:
                    tem_stats_time = db.query(GameTeamStats.game_id).filter(GameTeamStats.game_id == jogo.id).first()

                    if not tem_stats_time:
                        ids_sem_stats_times.append(jogo.id)

                    tem_stats_jogador = db.query(PlayerGameStats.game_id).filter(PlayerGameStats.game_id == jogo.id).first()
                    if not tem_stats_jogador:
                        ids_sem_stats_jogadores.append(jogo.id)

                total_times     = len(ids_sem_stats_times)
                total_jogadores = len(ids_sem_stats_jogadores)
                if total_times == 0 and total_jogadores == 0:
                    logger.warning(f"Nenhum jogo pendente —> temporada={temporada}")
                    continue

                logger.warning(
                    f"Jogos pendentes detectados —> temporada={temporada}, "
                    f"sem_stats_times={total_times}, sem_stats_jogadores={total_jogadores}"
                )

                erros_times     = 0
                erros_jogadores = 0
                for game_id in ids_sem_stats_times:
                    try:
                        carregar_stats_times_jogo(game_id=game_id)
                    except Exception as erro:
                        erros_times = erros_times + 1
                        logger.error(f"Erro ao reprocessar stats de times —> game_id={game_id}: {erro}")
                        continue

                for game_id in ids_sem_stats_jogadores:
                    try:
                        carregar_stats_jogador(game_id=game_id)
                    except Exception as erro:
                        erros_jogadores = erros_jogadores + 1
                        logger.error(f"Erro ao reprocessar stats de jogadores —> game_id={game_id}: {erro}")
                        continue

                logger.warning(
                    f"Reprocessamento concluido —> temporada={temporada}, "
                    f"times_ok={total_times - erros_times}, times_erro={erros_times}, "
                    f"jogadores_ok={total_jogadores - erros_jogadores}, jogadores_erro={erros_jogadores}"
                )

    temporadas = obter_temporadas()
    op_ligas = carregar_ligas_task(temporadas)
    op_temporadas = carregar_temporadas_task(temporadas)
    op_times = carregar_times_task(temporadas)
    op_jogadores = carregar_jogadores_task(temporadas)
    op_partidas = carregar_partidas_task(temporadas)
    op_stats_jog = carregar_stats_jogadores_task(temporadas)
    op_stats_times = carregar_stats_times_task(temporadas)
    op_pendentes = reprocessar_stats_pendentes_task(temporadas)
    temporadas >> op_ligas >> op_temporadas >> op_times >> op_jogadores >> op_partidas >> op_stats_jog >> op_stats_times >> op_pendentes

dag_instance = nba_backfill_historico()