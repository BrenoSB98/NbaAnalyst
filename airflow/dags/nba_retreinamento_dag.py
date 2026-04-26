import os
import sys
import logging

sys.path.insert(0, os.environ.get("AIRFLOW_BACKEND_PATH", "/opt/airflow/backend"))

from datetime import datetime, timedelta
from airflow.decorators import dag, task
from app.config import config

logger = logging.getLogger("nba_retreinamento_dag")

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
    dag_id="nba_retreinamento",
    default_args=args_padrao,
    description="Retreina todos os modelos do zero a cada 3 dias e gera relatorio PDF",
    schedule_interval="0 7 */3 * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["nba", "ml", "retreinamento"],
)
def nba_retreinamento():
    @task()
    def executar_treino():
        from app.db.db_utils import get_db
        from app.services.modelo_service import retreinar_todos_modelos
        from app.services.relatorio_service import gerar_e_salvar_relatorio

        logger.warning(f"Iniciando retreinamento completo: temporada={TEMPORADA_ATUAL}")

        resultado = None
        for db in get_db():
            resultado = retreinar_todos_modelos(db=db, season=TEMPORADA_ATUAL)

        if resultado is None:
            logger.warning(f"Retreinamento retornou None: temporada={TEMPORADA_ATUAL}")
            return

        total_salvos = resultado["total_salvos"]
        total_erros = resultado["total_erros"]
        total_jogadores = resultado["total_jogadores_treino"]
        total_registros = resultado["total_registros_db"]

        logger.warning(f"Retreinamento concluido: salvos={total_salvos}, erros={total_erros}, temporada={TEMPORADA_ATUAL}")

        try:
            for db in get_db():
                caminho_pdf = gerar_e_salvar_relatorio(db=db, season=TEMPORADA_ATUAL, total_registros_db=total_registros, total_jogadores_treino=total_jogadores, total_modelos_salvos=total_salvos, total_erros=total_erros)
                logger.warning(f"Relatorio gerado: {caminho_pdf}")
        except Exception as erro:
            logger.warning(f"Falha ao gerar relatorio: {erro}")

    executar_treino()

dag_instance = nba_retreinamento()