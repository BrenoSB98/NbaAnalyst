import os
import logging

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_community.tools.tavily_search import TavilySearchResults

from prompts import PROMPT_SISTEMA, MENSAGEM_ERRO_BANCO
from db_chat import buscar_contexto_geral
from base import buscar_na_base_conhecimento

logger = logging.getLogger(__name__)

chave_openai = os.getenv("OPENAI_API_KEY", "")
if chave_openai:
    os.environ["OPENAI_API_KEY"] = chave_openai
else:
    logger.warning("OPENAI_API_KEY nao encontrada nas variaveis de ambiente.")

MODELO_FIXO = "gpt-5-nano"

_ferramenta_busca = TavilySearchResults(max_results=3, name="buscar_na_internet")

def montar_historico_mensagens(historico, contexto_banco, contexto_conhecimento, pergunta):
    prompt_sistema_formatado = PROMPT_SISTEMA.format(contexto=contexto_banco, contexto_conhecimento=contexto_conhecimento )
    mensagens = [SystemMessage(content=prompt_sistema_formatado)]

    for entrada in historico:
        papel = entrada.get("papel")
        conteudo = entrada.get("conteudo")
        if papel == "usuario":
            mensagens.append(HumanMessage(content=conteudo))
        else:
            mensagens.append(AIMessage(content=conteudo))

    mensagens.append(HumanMessage(content=pergunta))
    return mensagens

def perguntar_ao_oraculo(pergunta, historico, modelo):
    try:
        contexto_banco = buscar_contexto_geral(pergunta)
    except Exception as erro:
        logger.error(f"Erro ao buscar contexto no banco: {erro}")
        return MENSAGEM_ERRO_BANCO

    if not contexto_banco:
        contexto_banco = ""

    try:
        contexto_conhecimento = buscar_na_base_conhecimento(pergunta, n_resultados=3)
    except Exception as erro:
        logger.error(f"Erro ao buscar na base de conhecimento: {erro}")
        contexto_conhecimento = ""

    if not contexto_conhecimento:
        contexto_conhecimento = ""

    mensagens = montar_historico_mensagens(historico, contexto_banco, contexto_conhecimento, pergunta)

    try:
        llm = ChatOpenAI(model=MODELO_FIXO, temperature=1)
        llm_com_ferramentas = llm.bind_tools([_ferramenta_busca])
        resposta_inicial = llm_com_ferramentas.invoke(mensagens)

        if not resposta_inicial.tool_calls:
            return resposta_inicial.content

        mensagens.append(resposta_inicial)

        for chamada in resposta_inicial.tool_calls:
            query = chamada["args"].get("query", "")
            logger.info(f"Buscando na internet: {query}")

            try:
                resultado_busca = _ferramenta_busca.invoke(query)
            except Exception as erro:
                logger.warning(f"Erro na busca: {erro}")
                resultado_busca = "Não foi possível buscar na internet no momento."

            mensagem_tool = ToolMessage(content=resultado_busca, tool_call_id=chamada["id"] )
            mensagens.append(mensagem_tool)

        resposta_final = llm.invoke(mensagens)
        return resposta_final.content

    except Exception as erro:
        logger.error(f"Erro ao chamar o LLM —> modelo={modelo}: {erro}")
        return "Ocorreu um erro ao consultar a LLM. Tente novamente."

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