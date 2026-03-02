import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import config
from app.db.db_utils import get_db
from app.services.manager_service import salvar_predicoes_dia_atual

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")

def job_gerar_predicoes():
    temporada = config.NBA_SEASON
    db = None
    try:
        for db in get_db():
            total = salvar_predicoes_dia_atual(db=db, season=temporada)
            logger.info(f"Predições geradas: {total}")
    except Exception as erro:
        logger.error(f"Erro no job de predições: {erro}")
    finally:
        if db:
            db.close()

def iniciar_scheduler():
    if scheduler.running:
        logger.warning("Scheduler já está rodando.")
        return

    scheduler.add_job(
        func=job_gerar_predicoes,
        trigger=CronTrigger(hour=8, minute=0),
        id="job_predicoes_diarias",
        name="Geração Diária de Predições",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    logger.info("Scheduler iniciado.")

def encerrar_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler encerrado.")