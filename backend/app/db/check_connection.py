from sqlalchemy import text

from app.db.session import engine
from app.db.base import Base
from app.db import models  # noqa: F401

def verificar_conexao():
    print("Verificando conexão com o banco de dados")
    try:
        with engine.connect() as conexao:
            resultado = conexao.execute(text("SELECT 1"))
            linha = resultado.fetchone()
            print(f"Conexão OK, resultado SELECT 1: {linha[0]}")
    except Exception as e:
        print("Erro ao conectar no banco de dados:")
        print(e)
        return

    print()
    print("Listando tabelas registradas no metadata:")
    try:
        for nome_tabela in Base.metadata.tables.keys():
            print(f"- {nome_tabela}")
    except Exception as exc:
        print("Erro ao acessar metadata das tabelas:")
        print(exc)
        return

if __name__ == "__main__":
    verificar_conexao()