import logging
import os
import time

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from prompts import MENSAGEM_ERRO_BANCO
from db_chat import buscar_contexto_geral
from base import obter_retriever

logger = logging.getLogger("oraculo")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

_llm = None
_retriever = None

def _obter_llm():
    global _llm
    if _llm is None:
        logger.warning(f"Inicializando LLM: modelo={OLLAMA_MODEL}, host={OLLAMA_HOST}")
        _llm = ChatOllama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_HOST,
            temperature=0.3,
            num_predict=100,
            num_ctx=2048,
            top_p=0.85,
            repeat_penalty=1.2,
        )
    return _llm

def _obter_retriever_cached():
    global _retriever
    if _retriever is None:
        _retriever = obter_retriever(n_resultados=2)
    return _retriever

def _truncar(texto, max_chars):
    if not texto:
        return ""
    if len(texto) <= max_chars:
        return texto
    return texto[:max_chars] + "..."

def _buscar_conhecimento_rag(pergunta):
    retriever = _obter_retriever_cached()
    if retriever is None:
        return ""
    try:
        docs = retriever.invoke(pergunta)
        if not docs:
            return ""
        partes = []
        for doc in docs:
            partes.append(_truncar(doc.page_content, 300))
        return "\n---\n".join(partes)
    except Exception as erro:
        logger.error(f"Erro no retriever RAG: {erro}")
        return ""

def _montar_prompt_sistema(contexto_banco, contexto_rag):
    partes = []
    partes.append("Você é o Onerb, assistente de basquete NBA. Responda em português, direto e curto (2-4 linhas).")
    partes.append("A temporada NBA vai de outubro a junho do ano seguinte (temporada 2025 = out/2025 a jun/2026).")
    partes.append("Nunca diga 'banco de dados', 'contexto' ou 'base de conhecimento'. Fale apenas do que foi perguntado.")

    if contexto_banco:
        partes.append("")
        partes.append("DADOS REAIS (use estes dados na resposta):")
        partes.append(contexto_banco)

    if contexto_rag:
        partes.append("")
        partes.append("INFORMAÇÕES NBA:")
        partes.append(contexto_rag)

    return "\n".join(partes)

def _converter_historico(historico):
    mensagens = []
    for entrada in historico:
        papel = entrada.get("papel")
        conteudo = entrada.get("conteudo", "")
        if papel == "usuario":
            mensagens.append(HumanMessage(content=conteudo))
        else:
            mensagens.append(AIMessage(content=conteudo))
    return mensagens

def perguntar_ao_oraculo(pergunta, historico, modelo=None):
    inicio_total = time.time()

    inicio_db = time.time()
    try:
        contexto_banco = buscar_contexto_geral(pergunta)
    except Exception as erro:
        logger.error(f"Erro ao buscar contexto no banco: {erro}")
        return MENSAGEM_ERRO_BANCO
    tempo_db = time.time() - inicio_db

    if not contexto_banco:
        contexto_banco = ""
    contexto_banco = _truncar(contexto_banco, 1200)
    logger.warning(f"Contexto banco: {len(contexto_banco)} chars, tempo={tempo_db:.2f}s")

    inicio_rag = time.time()
    contexto_rag = _buscar_conhecimento_rag(pergunta)
    tempo_rag = time.time() - inicio_rag
    logger.warning(f"Contexto RAG: {len(contexto_rag)} chars, tempo={tempo_rag:.4f}s")

    texto_sistema = _montar_prompt_sistema(contexto_banco, contexto_rag)

    mensagens = []
    mensagens.append(SystemMessage(content=texto_sistema))
    for msg in _converter_historico(historico):
        mensagens.append(msg)
    mensagens.append(HumanMessage(content=pergunta))

    logger.warning(f"Enviando para LLM: {len(mensagens)} msgs, sistema={len(texto_sistema)} chars")

    inicio_llm = time.time()
    try:
        llm = _obter_llm()
        resposta = llm.invoke(mensagens)
        tempo_llm = time.time() - inicio_llm
        tempo_total = time.time() - inicio_total
        logger.warning(f"LLM respondeu: tempo_llm={tempo_llm:.1f}s, total={tempo_total:.1f}s")
        return resposta.content
    except Exception as erro:
        logger.error(f"Erro ao invocar LLM: modelo={OLLAMA_MODEL}: {erro}")
        return "Serviço de IA temporariamente indisponível. Verifique se o container ollama está em execução."

def historico_para_exibicao(historico):
    mensagens_exibicao = []
    for entrada in historico:
        papel = entrada.get("papel")
        conteudo = entrada.get("conteudo")
        if papel == "usuario":
            mensagens_exibicao.append({"role": "user", "content": conteudo})
        else:
            mensagens_exibicao.append({"role": "assistant", "content": conteudo})
    return mensagens_exibicao

def adicionar_ao_historico(historico, papel, conteudo):
    historico.append({"papel": papel, "conteudo": conteudo})
    return historico

def limpar_historico():
    return []