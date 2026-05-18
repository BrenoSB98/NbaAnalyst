import logging
import os
import time

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool

from prompts import (
    PROMPT_SISTEMA_CHAT,
    DESC_BUSCAR_BANCO,
    DESC_BUSCAR_CONHECIMENTO,
    DESC_BUSCAR_WEB,
)
from db_chat import buscar_contexto_geral
from base import obter_retriever
from web_search import buscar_na_web

logger = logging.getLogger("oraculo")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

_llm = None
_retriever = None


def _obter_llm():
    global _llm
    if _llm is None:
        if not GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY não configurada. Adicione a variável no .env."
            )
        logger.warning(f"Inicializando LLM: Groq, modelo={GROQ_MODEL}")
        _llm = ChatGroq(
            model=GROQ_MODEL, api_key=GROQ_API_KEY, temperature=0.3, max_tokens=1500 # type: ignore
        )
    return _llm


def _obter_retriever_cached():
    global _retriever
    if _retriever is None:
        _retriever = obter_retriever(n_resultados=3)
    return _retriever


def _truncar(texto, max_chars):
    if not texto:
        return ""
    if len(texto) <= max_chars:
        return texto
    return texto[:max_chars] + "..."


@tool(description=DESC_BUSCAR_BANCO)
def buscar_banco(pergunta: str) -> str:
    """Busca no banco de dados."""
    try:
        resultado = buscar_contexto_geral(pergunta)
        if not resultado:
            return "Nenhum dado encontrado no banco para essa pergunta."
        return _truncar(resultado, 1200)
    except Exception as erro:
        logger.error(f"Erro na ferramenta buscar_banco: {erro}")
        return "Erro ao consultar o banco de dados."


@tool(description=DESC_BUSCAR_CONHECIMENTO)
def buscar_conhecimento_nba(pergunta: str) -> str:
    """Busca nos documentos de conhecimento NBA."""
    retriever = _obter_retriever_cached()
    if retriever is None:
        return ""
    try:
        docs = retriever.invoke(pergunta)
        if not docs:
            return ""
        partes = []
        for doc in docs:
            partes.append(_truncar(doc.page_content, 400))
        return "\n---\n".join(partes)
    except Exception as erro:
        logger.error(f"Erro na ferramenta buscar_conhecimento_nba: {erro}")
        return ""


@tool(description=DESC_BUSCAR_WEB)
def buscar_web(pergunta: str) -> str:
    """Busca na internet."""
    if not TAVILY_API_KEY:
        return "Busca web não configurada."
    resultado = buscar_na_web(pergunta)
    if not resultado:
        return "Nenhuma informação recente encontrada."
    return _truncar(resultado, 2000)


_FERRAMENTAS = [buscar_banco, buscar_conhecimento_nba, buscar_web]

_MAPA_FERRAMENTAS = {
    "buscar_banco": buscar_banco,
    "buscar_conhecimento_nba": buscar_conhecimento_nba,
    "buscar_web": buscar_web,
}


def _executar_ferramentas(tool_calls):
    resultados = []
    for tc in tool_calls:
        nome = tc["name"]
        args = tc["args"]
        tool_id = tc["id"]
        ferramenta = _MAPA_FERRAMENTAS.get(nome)
        if ferramenta is None:
            logger.error(f"Ferramenta desconhecida: {nome}")
            resultados.append(
                ToolMessage(content="Ferramenta não encontrada.", tool_call_id=tool_id)
            )
            continue
        inicio = time.time()
        try:
            resultado = ferramenta.invoke(args)
            resultado = _truncar(str(resultado), 1200)
        except Exception as erro:
            logger.error(f"Erro ao executar {nome}: {erro}")
            resultado = "Erro ao executar a ferramenta."
        tempo = time.time() - inicio
        logger.warning(f"Ferramenta {nome}: {len(resultado)} chars, tempo={tempo:.2f}s")
        resultados.append(ToolMessage(content=resultado, tool_call_id=tool_id))
    return resultados


def _converter_historico(historico):
    mensagens = []
    historico_recente = historico[-6:] if len(historico) > 6 else historico
    for entrada in historico_recente:
        papel = entrada.get("papel")
        conteudo = entrada.get("conteudo", "")
        if papel == "usuario":
            mensagens.append(HumanMessage(content=conteudo))
        else:
            mensagens.append(AIMessage(content=conteudo))
    return mensagens


def perguntar_ao_oraculo(pergunta, historico, modelo=None):
    inicio_total = time.time()
    try:
        llm = _obter_llm()

        mensagens = []
        mensagens.append(SystemMessage(content=PROMPT_SISTEMA_CHAT))
        for msg in _converter_historico(historico):
            mensagens.append(msg)
        mensagens.append(HumanMessage(content=pergunta))

        logger.warning(f"Groq: enviando {len(mensagens)} msgs")

        llm_com_tools = llm.bind_tools(_FERRAMENTAS)
        inicio_round1 = time.time()
        resposta = llm_com_tools.invoke(mensagens)
        logger.warning(
            f"Groq: round 1 em {time.time() - inicio_round1:.2f}s, tool_calls={len(resposta.tool_calls)}, chars={len(resposta.content)}"
        )

        if not resposta.tool_calls:
            logger.warning(f"Groq: total={time.time() - inicio_total:.2f}s")
            if resposta.content:
                return resposta.content
            return "Não encontrei informações suficientes sobre isso."

        mensagens.append(resposta)
        resultados_tools = _executar_ferramentas(resposta.tool_calls)
        for tr in resultados_tools:
            mensagens.append(tr)

        llm_sem_tools = llm.bind_tools(_FERRAMENTAS, tool_choice="none")
        inicio_round2 = time.time()
        resposta_final = llm_sem_tools.invoke(mensagens)
        logger.warning(
            f"Groq: round 2 em {time.time() - inicio_round2:.2f}s, chars={len(resposta_final.content)}, total={time.time() - inicio_total:.2f}s"
        )

        if resposta_final.content:
            return resposta_final.content
        return "Não encontrei informações suficientes sobre isso."

    except RuntimeError as erro:
        logger.error(f"Configuração inválida: {erro}")
        return str(erro)
    except Exception as erro:
        erro_str = str(erro)
        if "tool_use_failed" in erro_str or "failed_generation" in erro_str:
            logger.error(f"Groq: tool_use_failed: {erro}")
            return "Não consegui processar essa pergunta. Tente reformulá-la com mais detalhes."
        logger.error(f"Erro no pipeline Groq: {erro}")
        return (
            "Serviço de IA temporariamente indisponível. Tente novamente em instantes."
        )


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
