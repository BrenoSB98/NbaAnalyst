from sqlalchemy import text

from app.db.session import engine
from app.db.base import Base
from app.db import models  # noqa: F401


def check_connection():
    print("Verificando conexão com o banco de dados")
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            row = result.fetchone()
            print(f"Conexão OK, resultado SELECT 1: {row[0]}")
    except Exception as exc:
        print("Erro ao conectar no banco de dados:")
        print(exc)
        return

    print()
    print("Listando tabelas registradas no metadata:")
    try:
        for table_name in Base.metadata.tables.keys():
            print(f"- {table_name}")
    except Exception as exc:
        print("Erro ao acessar metadata das tabelas:")
        print(exc)


if __name__ == "__main__":
    check_connection()