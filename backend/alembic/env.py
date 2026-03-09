import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from app.config import config as app_config  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db import models  # noqa: F401, E402

alembic_config = context.config

if alembic_config.config_file_name is not None:
    fileConfig(alembic_config.config_file_name)

target_metadata = Base.metadata

TABELAS_AIRFLOW = {
    "ab_role", "ab_user", "ab_user_role", "ab_permission", "ab_view_menu",
    "ab_permission_view", "ab_permission_view_role", "ab_register_user",
    "dag", "dag_run", "dag_code", "dag_tag", "dag_pickle", "dag_warning",
    "dag_owner_attributes", "dag_schedule_dataset_reference",
    "dag_run_note", "task_instance", "task_instance_note", "task_fail",
    "task_reschedule", "task_map", "task_outlet_dataset_reference",
    "rendered_task_instance_fields", "xcom", "log", "log_template",
    "job", "slot_pool", "connection", "variable", "session",
    "serialized_dag", "import_error", "sla_miss", "trigger",
    "dataset", "dataset_event", "dataset_dag_run_queue",
    "dagrun_dataset_event", "callback_request",
}

def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and name in TABELAS_AIRFLOW:
        return False
    return True

def get_url():
    return app_config.DATABASE_URL

def run_migrations_offline():
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    configuration = alembic_config.get_section(alembic_config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()