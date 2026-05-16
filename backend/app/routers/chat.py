import logging
import sys
import os
import time
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
        "restantes_hoje": restantes,
        "modelo": config.OLLAMA_MODEL,
    }

@router.get("/diagnostico")
def diagnostico_chat(pergunta: str, usuario_atual=Depends(obter_usuario_atual)):
    try:
        from db_chat import buscar_contexto_geral, _extrair_possiveis_times, _extrair_possiveis_nomes, _extrair_mes_ano, _extrair_temporadas
        from base import buscar_na_base_conhecimento
    except ImportError as erro:
        return {"erro": f"Falha ao importar modulos chat: {erro}"}

    inicio = time.time()
    pergunta_lower = pergunta.lower()

    times = _extrair_possiveis_times(pergunta_lower)
    nomes = _extrair_possiveis_nomes(pergunta_lower)
    mes, ano = _extrair_mes_ano(pergunta_lower)
    temporadas = _extrair_temporadas(pergunta_lower)

    contexto_banco = buscar_contexto_geral(pergunta)
    tempo_banco = time.time() - inicio

    inicio_rag = time.time()
    contexto_rag = buscar_na_base_conhecimento(pergunta, n_resultados=2)
    tempo_rag = time.time() - inicio_rag

    return {
        "pergunta": pergunta,
        "extracao": {
            "times": times,
            "nomes": nomes,
            "mes_ano": f"{mes}/{ano}",
            "temporadas": temporadas,
        },
        "contexto_banco": {
            "chars": len(contexto_banco),
            "tempo_segundos": round(tempo_banco, 3),
            "preview": contexto_banco[:500] if contexto_banco else "(vazio)",
        },
        "contexto_rag": {
            "chars": len(contexto_rag),
            "tempo_segundos": round(tempo_rag, 5),
            "preview": contexto_rag[:300] if contexto_rag else "(vazio)",
        },
        "modelo": config.OLLAMA_MODEL,
        "ollama_host": config.OLLAMA_HOST,
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
        logger.error(f"Falha ao importar modulo oraculo: {erro}")
        raise HTTPException(status_code=503, detail="Serviço de chat indisponível no momento.")

    historico_convertido = []
    for entrada in (dados.historico or []):
        historico_convertido.append({"papel": entrada.papel, "conteudo": entrada.conteudo})

    try:
        resposta = perguntar_ao_oraculo(pergunta=dados.pergunta, historico=historico_convertido)
    except Exception as erro:
        logger.error(f"Erro ao consultar o modelo: {erro}")
        raise HTTPException(status_code=500, detail="Erro ao consultar o modelo de linguagem.")

    _incrementar_contagem(usuario_atual.id)
    return {"resposta": resposta}