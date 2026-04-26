import os
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.db_utils import get_db
from app.routers.auth import obter_usuario_admin

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


@router.post("/retreinar")
def retreinar_manualmente(db: Session = Depends(get_db), usuario=Depends(obter_usuario_admin)):
    from app.config import config
    from app.services.modelo_service import retreinar_todos_modelos
    from app.services.relatorio_service import gerar_e_salvar_relatorio

    season = config.NBA_SEASON

    resultado = retreinar_todos_modelos(db=db, season=season)

    caminho_pdf = None
    try:
        caminho_pdf = gerar_e_salvar_relatorio(db=db, season=season, total_registros_db=resultado["total_registros_db"], total_jogadores_treino=resultado["total_jogadores_treino"], total_modelos_salvos=resultado["total_salvos"], total_erros=resultado["total_erros"])
    except Exception as erro:
        logger.warning(f"Falha ao gerar relatorio apos retreino manual: {erro}")

    nome_pdf = os.path.basename(caminho_pdf) if caminho_pdf else None

    return {
        "mensagem": "Retreinamento concluido",
        "modelos_salvos": resultado["total_salvos"],
        "erros": resultado["total_erros"],
        "jogadores_treinados": resultado["total_jogadores_treino"],
        "relatorio_gerado": nome_pdf,
    }