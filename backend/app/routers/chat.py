import logging
import sys
import os
from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from app.config import config
from app.routers.auth import obter_usuario_atual
from app.schemas.onerb import RequisicaoChat, RespostaChat

router = APIRouter()
logger = logging.getLogger(__name__)

CHAT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "chat")
if CHAT_DIR not in sys.path:
    sys.path.insert(0, CHAT_DIR)

MODELO = "gpt-5-nano"

_contagem_diaria = {}
def _obter_contagem(user_id):
    hoje = str(date.today())
    chave = str(user_id)

    if chave not in _contagem_diaria:
        _contagem_diaria[chave] = {}

    if _contagem_diaria[chave].get("data") != hoje:
        _contagem_diaria[chave] = {"data": hoje, "total": 0}

    return _contagem_diaria[chave]["total"]

def _incrementar_contagem(user_id):
    hoje = str(date.today())
    chave = str(user_id)

    if chave not in _contagem_diaria:
        _contagem_diaria[chave] = {}

    if _contagem_diaria[chave].get("data") != hoje:
        _contagem_diaria[chave] = {"data": hoje, "total": 0}

    _contagem_diaria[chave]["total"] = _contagem_diaria[chave]["total"] + 1

@router.get("/limite")
def obter_limite(usuario_atual=Depends(obter_usuario_atual)):
    usadas = _obter_contagem(usuario_atual.id)
    limite = config.LIMITE_MENSAGENS_CHAT_DIA
    restantes = max(0, limite - usadas)
    return {
        "limite_diario": limite,
        "usadas_hoje": usadas,
        "restantes_hoje": restantes
    }

@router.post("/mensagem", response_model=RespostaChat)
def enviar_mensagem(dados: RequisicaoChat, usuario_atual=Depends(obter_usuario_atual)):
    limite = config.LIMITE_MENSAGENS_CHAT_DIA
    usadas = _obter_contagem(usuario_atual.id)

    if usadas >= limite:
        raise HTTPException(status_code=429, detail=f"Limite diário de {limite} perguntas atingido. Tente novamente amanhã.")

    try:
        from oraculo import perguntar_ao_oraculo
    except ImportError as erro:
        logger.error(f"Falha ao importar módulo oraculo: {erro}")
        raise HTTPException(status_code=503, detail="Serviço de chat indisponível no momento.")

    historico_convertido = []
    for entrada in (dados.historico or []):
        historico_convertido.append({"papel": entrada.papel, "conteudo": entrada.conteudo})
 
    try:
        resposta = perguntar_ao_oraculo(pergunta=dados.pergunta, historico=historico_convertido, modelo=MODELO)
    except Exception as erro:
        logger.error(f"Erro ao consultar o LLM: {erro}")
        raise HTTPException(status_code=500, detail="Erro ao consultar o modelo de linguagem. Tente novamente.")
 
    _incrementar_contagem(usuario_atual.id)
    return {"resposta": resposta}