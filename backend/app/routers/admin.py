import os
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.db_utils import get_db
from app.routers.auth import obter_usuario_admin
from app.services.relatorio_service import carregar_metadados_anterior

logger = logging.getLogger("admin_router")

router = APIRouter()

def _pasta_relatorios():
    from app.config import config
    return config.PASTA_RELATORIOS

def _listar_pdfs():
    pasta = _pasta_relatorios()
    if not os.path.exists(pasta):
        return []

    arquivos = os.listdir(pasta)
    pdfs = []

    for nome in arquivos:
        if not nome.endswith(".pdf"):
            continue
        if not nome.startswith("relatorio_"):
            continue

        caminho = os.path.join(pasta, nome)
        tamanho = os.path.getsize(caminho)
        data_modificacao = os.path.getmtime(caminho)

        item = {}
        item["nome"] = nome
        item["tamanho_bytes"] = tamanho
        item["data_modificacao"] = data_modificacao
        pdfs.append(item)

    pdfs.sort(key=lambda x: x["data_modificacao"], reverse=True)
    return pdfs

@router.get("/relatorios")
def listar_relatorios(usuario=Depends(obter_usuario_admin)):
    pdfs = _listar_pdfs()
    lista = []

    for pdf in pdfs:
        item = {}
        item["nome"] = pdf["nome"]
        item["tamanho_kb"] = round(pdf["tamanho_bytes"] / 1024, 1)
        item["data_modificacao"] = pdf["data_modificacao"]
        lista.append(item)

    return {"relatorios": lista, "total": len(lista)}

@router.get("/relatorios/ultimo")
def baixar_ultimo_relatorio(usuario=Depends(obter_usuario_admin)):
    pdfs = _listar_pdfs()

    if not pdfs:
        raise HTTPException(status_code=404, detail="Nenhum relatorio encontrado")

    mais_recente = pdfs[0]
    pasta = _pasta_relatorios()
    caminho = os.path.join(pasta, mais_recente["nome"])

    return FileResponse(path=caminho, filename=mais_recente["nome"], media_type="application/pdf")

@router.get("/relatorios/download/{nome_arquivo}")
def baixar_relatorio(nome_arquivo: str, usuario=Depends(obter_usuario_admin)):
    if ".." in nome_arquivo or "/" in nome_arquivo or "\\" in nome_arquivo:
        raise HTTPException(status_code=400, detail="Nome de arquivo invalido")

    if not nome_arquivo.endswith(".pdf") or not nome_arquivo.startswith("relatorio_"):
        raise HTTPException(status_code=400, detail="Arquivo nao permitido")

    pasta = _pasta_relatorios()
    caminho = os.path.join(pasta, nome_arquivo)

    if not os.path.exists(caminho):
        raise HTTPException(status_code=404, detail="Relatorio nao encontrado")

    return FileResponse(path=caminho, filename=nome_arquivo, media_type="application/pdf")

def _executar_retreino_background(season):
    from app.db.session import SessionLocal
    from app.services.modelo_service import retreinar_todos_modelos
    from app.services.relatorio_service import gerar_e_salvar_relatorio

    db = SessionLocal()
    try:
        logger.warning(f"Retreinamento em background iniciado: temporada={season}")
        resultado = retreinar_todos_modelos(db=db, season=season)

        logger.warning(f"Gerando relatorio PDF: temporada={season}")
        caminho_pdf = gerar_e_salvar_relatorio(db=db, season=season, total_registros_db=resultado["total_registros_db"], total_jogadores_treino=resultado["total_jogadores_treino"], total_modelos_salvos=resultado["total_salvos"], total_erros=resultado["total_erros"])
        logger.warning(f"Relatorio gerado: {caminho_pdf}")
    except Exception as erro:
        logger.warning(f"Erro no retreinamento em background: temporada={season}: {erro}")
    finally:
        db.close()

@router.post("/retreinar")
def retreinar_manualmente(background_tasks: BackgroundTasks, usuario=Depends(obter_usuario_admin)):
    from app.config import config

    season = config.NBA_SEASON
    background_tasks.add_task(_executar_retreino_background, season)

    return {
        "mensagem": "Retreinamento iniciado em background. O relatório PDF será gerado ao final.",
        "temporada": season,
        "em_andamento": True,
    }

@router.get("/info")
def obter_info_admin(usuario=Depends(obter_usuario_admin)):
    from app.config import config
    import glob

    pasta_modelos = config.PASTA_MODELOS
    total_modelos = 0

    if os.path.exists(pasta_modelos):
        arquivos = glob.glob(os.path.join(pasta_modelos, "*.pkl"))
        total_modelos = len(arquivos)

    ultimo_treino = carregar_metadados_anterior()
    data_ultimo_treino = None
    modelos_salvos_ultimo = None

    if ultimo_treino is not None:
        data_ultimo_treino = ultimo_treino.get("data_geracao", None)
        modelos_salvos_ultimo = ultimo_treino.get("total_salvos", None)

    return {
        "total_modelos": total_modelos,
        "data_ultimo_treino": data_ultimo_treino,
        "modelos_salvos_ultimo_treino": modelos_salvos_ultimo,
    }