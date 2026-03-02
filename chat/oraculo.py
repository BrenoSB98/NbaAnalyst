import os
from decouple import config as env

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from prompts import PROMPT_SISTEMA, MENSAGEM_SEM_CONTEXTO, MENSAGEM_ERRO_BANCO
from db_chat import buscar_contexto_geral

os.environ["OPENAI_API_KEY"] = env("OPENAI_API_KEY")

MODELOS_DISPONIVEIS = [
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4-turbo",
    "gpt-4",
    "gpt-3.5-turbo",
]

def montar_historico_mensagens(historico, contexto, pergunta):
    prompt_sistema_formatado = PROMPT_SISTEMA.format(contexto=contexto)
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
        contexto = buscar_contexto_geral(pergunta)
    except Exception:
        return MENSAGEM_ERRO_BANCO
    if not contexto:
        contexto = MENSAGEM_SEM_CONTEXTO
    mensagens = montar_historico_mensagens(historico, contexto, pergunta)
    try:
        llm = ChatOpenAI(model=modelo, temperature=0.3)
        resposta = llm.invoke(mensagens)
        return resposta.content
    except Exception:
        return "Ocorreu um erro ao consultar o modelo de linguagem. Tente novamente."

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