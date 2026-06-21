import logging
import os
import time

import db_chat
from base import obter_retriever
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from prompts import (
    DESC_BUSCAR_CONHECIMENTO,
    DESC_BUSCAR_WEB,
    DESC_CLASSIFICACAO,
    DESC_COMPARAR_JOGADORES,
    DESC_JOGOS_TIME,
    DESC_LIDERES_LIGA,
    DESC_STATS_JOGADOR,
    PROMPT_SISTEMA_CHAT,
)
from web_search import buscar_na_web

logger = logging.getLogger("oraculo")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

LIMITE_TOKENS_INPUT = 30000
LIMITE_TOKENS_SESSAO = 200000
CHARS_POR_TOKEN = 4

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
            model=GROQ_MODEL,
            api_key=GROQ_API_KEY,  # type: ignore
            temperature=0.3,
            max_tokens=2000,
            reasoning_effort="low",
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


def _estimar_tokens(texto):
    if not texto:
        return 0
    return max(1, len(str(texto)) // CHARS_POR_TOKEN)


def _tokens_mensagens(mensagens):
    total = 0
    for m in mensagens:
        total = total + _estimar_tokens(getattr(m, "content", ""))
    return total


def _truncar_historico_para_limite(historico, system_prompt, pergunta_atual, limite):
    tokens_fixos = _estimar_tokens(system_prompt) + _estimar_tokens(pergunta_atual)
    orcamento = limite - tokens_fixos
    if orcamento <= 0:
        return []
    historico_invertido = list(reversed(historico))
    selecionados = []
    acumulado = 0
    for entrada in historico_invertido:
        custo = _estimar_tokens(entrada.get("conteudo", ""))
        if acumulado + custo > orcamento:
            break
        selecionados.append(entrada)
        acumulado = acumulado + custo
    selecionados.reverse()
    descartadas = len(historico) - len(selecionados)
    if descartadas > 0:
        logger.warning(
            f"Histórico truncado: descartadas {descartadas} mensagens antigas"
        )
    return selecionados


@tool(description=DESC_STATS_JOGADOR)
def stats_jogador_temporada(nome_jogador: str, temporada: int) -> str:
    """Stats de um jogador em uma temporada."""
    try:
        resultado = db_chat.stats_jogador_temporada(nome_jogador, temporada)
        return _truncar(resultado, 1500)
    except Exception as erro:
        logger.error(f"Erro stats_jogador_temporada: {erro}")
        return "Erro ao consultar estatísticas do jogador."


@tool(description=DESC_JOGOS_TIME)
def jogos_time(nome_time: str, ano: int, mes: int = 0) -> str:
    """Jogos de um time por mês ou temporada."""
    try:
        mes_param = mes if mes > 0 else None
        resultado = db_chat.jogos_time(nome_time, ano, mes_param)
        return _truncar(resultado, 1500)
    except Exception as erro:
        logger.error(f"Erro jogos_time: {erro}")
        return "Erro ao consultar jogos do time."


@tool(description=DESC_LIDERES_LIGA)
def lideres_liga(estatistica: str, temporada: int, top_n: int = 10) -> str:
    """Líderes da liga em uma estatística."""
    try:
        resultado = db_chat.lideres_liga(estatistica, temporada, top_n)
        return _truncar(resultado, 1500)
    except Exception as erro:
        logger.error(f"Erro lideres_liga: {erro}")
        return "Erro ao consultar líderes da liga."


@tool(description=DESC_COMPARAR_JOGADORES)
def comparar_jogadores(nomes: list, temporada: int) -> str:
    """Compara estatísticas de jogadores na mesma temporada."""
    try:
        resultado = db_chat.comparar_jogadores(nomes, temporada)
        return _truncar(resultado, 1500)
    except Exception as erro:
        logger.error(f"Erro comparar_jogadores: {erro}")
        return "Erro ao comparar jogadores."


@tool(description=DESC_CLASSIFICACAO)
def classificacao_temporada(conferencia: str, temporada: int) -> str:
    """Classificação dos times na temporada."""
    try:
        resultado = db_chat.classificacao_temporada(conferencia, temporada)
        return _truncar(resultado, 1500)
    except Exception as erro:
        logger.error(f"Erro classificacao_temporada: {erro}")
        return "Erro ao consultar classificação."


@tool(description=DESC_BUSCAR_CONHECIMENTO)
def buscar_conhecimento_nba(pergunta: str) -> str:
    """Busca em documentos conceituais sobre a NBA."""
    retriever = _obter_retriever_cached()
    if retriever is None:
        return ""
    try:
        docs = retriever.invoke(pergunta)
        if not docs:
            return "Nenhum documento relevante encontrado."
        partes = []
        for doc in docs:
            partes.append(_truncar(doc.page_content, 400))
        return "\n\n".join(partes)
    except Exception as erro:
        logger.error(f"Erro buscar_conhecimento_nba: {erro}")
        return ""


@tool(description=DESC_BUSCAR_WEB)
def buscar_web(pergunta: str) -> str:
    """Busca informações atuais na internet."""
    if not TAVILY_API_KEY:
        return "Busca web não configurada."
    resultado = buscar_na_web(pergunta)
    if not resultado:
        return "Nenhuma informação recente encontrada."
    return _truncar(resultado, 2000)


_FERRAMENTAS = [
    stats_jogador_temporada,
    jogos_time,
    lideres_liga,
    comparar_jogadores,
    classificacao_temporada,
    buscar_conhecimento_nba,
    buscar_web,
]

_MAPA_FERRAMENTAS = {
    "stats_jogador_temporada": stats_jogador_temporada,
    "jogos_time": jogos_time,
    "lideres_liga": lideres_liga,
    "comparar_jogadores": comparar_jogadores,
    "classificacao_temporada": classificacao_temporada,
    "buscar_conhecimento_nba": buscar_conhecimento_nba,
    "buscar_web": buscar_web,
}


def _executar_ferramentas(tool_calls):
    MAX_CALLS = 2
    resultados = []
    chamadas_a_executar = tool_calls[:MAX_CALLS]
    if len(tool_calls) > MAX_CALLS:
        logger.warning(f"Limitando {len(tool_calls)} ferramentas para {MAX_CALLS}")
        for tc in tool_calls[MAX_CALLS:]:
            resultados.append(
                ToolMessage(
                    content="Use os resultados das outras ferramentas para responder.",
                    tool_call_id=tc["id"],
                )
            )
    for tc in chamadas_a_executar:
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
            resultado = _truncar(str(resultado), 2000)
        except Exception as erro:
            logger.error(f"Erro ao executar {nome}: {erro}")
            resultado = "Erro ao executar a ferramenta."
        tempo = time.time() - inicio
        logger.warning(
            f"Ferramenta {nome}({args}): {len(resultado)} chars, tempo={tempo:.2f}s"
        )
        resultados.append(ToolMessage(content=resultado, tool_call_id=tool_id))
    return resultados


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


def perguntar_ao_oraculo(pergunta, historico, modelo=None, tokens_sessao=0):
    if tokens_sessao >= LIMITE_TOKENS_SESSAO:
        logger.warning(
            f"Sessão atingiu limite: {tokens_sessao} >= {LIMITE_TOKENS_SESSAO}"
        )
        return "Esta conversa atingiu o limite de uso. Recarregue a página ou faça logout/login para iniciar uma nova sessão."

    inicio_total = time.time()
    try:
        llm = _obter_llm()
        llm_com_tools = llm.bind_tools(_FERRAMENTAS)
        llm_sem_tools = llm.bind_tools(_FERRAMENTAS, tool_choice="none")

        historico_ajustado = _truncar_historico_para_limite(
            historico, PROMPT_SISTEMA_CHAT, pergunta, LIMITE_TOKENS_INPUT
        )

        mensagens = []
        mensagens.append(SystemMessage(content=PROMPT_SISTEMA_CHAT))
        for msg in _converter_historico(historico_ajustado):
            mensagens.append(msg)
        mensagens.append(HumanMessage(content=pergunta))

        tokens_input = _tokens_mensagens(mensagens)
        logger.warning(
            f"Groq: {len(mensagens)} msgs, ~{tokens_input} tokens, sessão={tokens_sessao}/{LIMITE_TOKENS_SESSAO}"
        )

        inicio_r1 = time.time()
        resposta = llm_com_tools.invoke(mensagens)
        tempo_r1 = time.time() - inicio_r1
        logger.warning(
            f"Groq: round 1 em {tempo_r1:.2f}s, tool_calls={len(resposta.tool_calls)}, chars={len(resposta.content)}"
        )

        if not resposta.tool_calls:
            tempo_total = time.time() - inicio_total
            logger.warning(f"Groq: encerrado sem tools, total={tempo_total:.2f}s")
            if resposta.content:
                return resposta.content
            return "Não encontrei informações suficientes sobre isso."

        mensagens.append(resposta)
        resultados_tools = _executar_ferramentas(resposta.tool_calls)
        for tr in resultados_tools:
            mensagens.append(tr)

        inicio_r2 = time.time()
        resposta_final = llm_sem_tools.invoke(mensagens)
        tempo_r2 = time.time() - inicio_r2
        tempo_total = time.time() - inicio_total
        logger.warning(
            f"Groq: round 2 em {tempo_r2:.2f}s, chars={len(resposta_final.content)}, total={tempo_total:.2f}s"
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
        if "rate_limit" in erro_str or "Rate limit" in erro_str:
            logger.error(f"Groq: rate limit atingido: {erro}")
            return "O serviço atingiu o limite de uso temporário. Aguarde alguns minutos e tente novamente."
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


def estimar_tokens_troca(pergunta, resposta):
    return _estimar_tokens(pergunta) + _estimar_tokens(resposta)
