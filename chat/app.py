import sys
import os

import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from oraculo import perguntar_ao_oraculo, adicionar_ao_historico, limpar_historico, MODELOS_DISPONIVEIS
from prompts import MENSAGEM_BOAS_VINDAS

st.set_page_config(
    page_title="Oráculo NBA",
    page_icon="🏀",
    layout="centered",
)

st.title("🏀 Oráculo NBA")
st.caption("Converse com o assistente especializado em dados históricos da NBA.")

with st.sidebar:
    st.header("⚙️ Configurações")

    modelo_selecionado = st.selectbox(
        label="Modelo LLM",
        options=MODELOS_DISPONIVEIS,
    )

    st.divider()

    if st.button("🗑️ Limpar conversa", use_container_width=True):
        st.session_state["historico"] = limpar_historico()
        st.rerun()

    st.divider()
    st.markdown("**Exemplos de perguntas:**")
    st.markdown("- Quais times estão disponíveis?")
    st.markdown("- Qual a média de pontos do LeBron James na temporada 2023?")
    st.markdown("- Mostre os jogos do Lakers na temporada 2022.")
    st.markdown("- Quais temporadas estão disponíveis?")

if "historico" not in st.session_state:
    st.session_state["historico"] = []

if not st.session_state["historico"]:
    st.chat_message("assistant").write(MENSAGEM_BOAS_VINDAS)

for entrada in st.session_state["historico"]:
    papel = entrada.get("papel")
    conteudo = entrada.get("conteudo")

    if papel == "usuario":
        st.chat_message("user").write(conteudo)
    else:
        st.chat_message("assistant").write(conteudo)

pergunta = st.chat_input("Faça sua pergunta sobre a NBA...")

if pergunta:
    st.chat_message("user").write(pergunta)

    st.session_state["historico"] = adicionar_ao_historico(
        st.session_state["historico"], "usuario", pergunta
    )

    with st.spinner("Consultando o Oráculo..."):
        resposta = perguntar_ao_oraculo(
            pergunta=pergunta,
            historico=st.session_state["historico"],
            modelo=modelo_selecionado,
        )

    st.chat_message("assistant").write(resposta)

    st.session_state["historico"] = adicionar_ao_historico(
        st.session_state["historico"], "oraculo", resposta
    )