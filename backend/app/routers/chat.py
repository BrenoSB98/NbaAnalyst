import logging
import sys
import os

from fastapi import APIRouter, Depends, HTTPException

from app.routers.auth import obter_usuario_atual
from app.schemas.onerb import RequisicaoChat, RespostaChat

router = APIRouter()
logger = logging.getLogger(__name__)

CHAT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "chat")
if CHAT_DIR not in sys.path:
    sys.path.insert(0, CHAT_DIR)

MODELOS_DISPONIVEIS = [
    "gpt-4o-mini"
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4-turbo",
    "gpt-4",
    "gpt-3.5-turbo",
]

@router.get("/modelos")
def listar_modelos(usuario_atual=Depends(obter_usuario_atual)):
    return {"modelos": MODELOS_DISPONIVEIS}


@router.post("/mensagem", response_model=RespostaChat)
def enviar_mensagem(dados: RequisicaoChat, usuario_atual=Depends(obter_usuario_atual)):
    try:
        from oraculo import perguntar_ao_oraculo
    except ImportError as erro:
        logger.error(f"Falha ao importar módulo oraculo: {erro}")
        raise HTTPException(status_code=503, detail="Serviço de chat indisponível no momento.")

    historico_convertido = []
    for entrada in (dados.historico or []):
        historico_convertido.append({"papel": entrada.papel, "conteudo": entrada.conteudo})

    try:
        resposta = perguntar_ao_oraculo(pergunta=dados.pergunta, historico=historico_convertido, modelo=dados.modelo or "gpt-5.1")
    except Exception as erro:
        logger.error(f"Erro ao consultar o LLM: {erro}")
        raise HTTPException(status_code=500, detail="Erro ao consultar o modelo de linguagem. Tente novamente.")
    return {"resposta": resposta}