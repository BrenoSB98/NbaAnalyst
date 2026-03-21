import os
import logging
 
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
 
from prompts import PROMPT_SISTEMA, MENSAGEM_SEM_CONTEXTO, MENSAGEM_ERRO_BANCO
from db_chat import buscar_contexto_geral
 
logger = logging.getLogger(__name__)
 
chave_openai = os.getenv("OPENAI_API_KEY", "")
if chave_openai:
    os.environ["OPENAI_API_KEY"] = chave_openai
else:
    logger.warning("OPENAI_API_KEY nao encontrada nas variaveis de ambiente.")

MODELOS_DISPONIVEIS = [
    "gpt-5"
    "gpt-5-mini",
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4o",
    "gpt-4o-mini",
]

def montar_historico_mensagens(historico, contexto, pergunta):
    prompt_sistema_formatado = PROMPT_SISTEMA.format(contexto=contexto)
    mensagens = [SystemMessage(content=prompt_sistema_formatado)]
    for entrada in historico:
        papel   = entrada.get("papel")
        conteudo = entrada.get("conteudo")
        if papel == "usuario":
            mensagens.append(HumanMessage(content=conteudo))
        else:
            mensagens.append(AIMessage(content=conteudo))
    mensagens.append(HumanMessage(content=pergunta))
    return mensagens
 
def perguntar_ao_oraculo(pergunta, historico, modelo):
    try:
        contexto = buscar_contexto_geral(pergunta)
    except Exception as erro:
        logger.error(f"Erro ao buscar contexto no banco: {erro}")
        return MENSAGEM_ERRO_BANCO
 
    if not contexto:
        contexto = MENSAGEM_SEM_CONTEXTO
 
    mensagens = montar_historico_mensagens(historico, contexto, pergunta)
 
    try:
        llm = ChatOpenAI(model=modelo)
        resposta = llm.invoke(mensagens)
        return resposta.content
    except Exception as erro:
        logger.error(f"Erro ao chamar o LLM —> modelo={modelo}: {erro}")
        return "Ocorreu um erro ao consultar a LLM. Tente novamente."
 
def historico_para_exibicao(historico):
    mensagens_exibicao = []
    for entrada in historico:
        papel   = entrada.get("papel")
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