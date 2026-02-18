import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
APP_PKG_DIR = os.path.join(BACKEND_DIR, "app")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

if APP_PKG_DIR not in sys.path:
    sys.path.insert(0, APP_PKG_DIR)
    
from app.db.session import SessionLocal
from app.db.models import Game, Team, GameTeamScore

import streamlit as st
from decouple import config

from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)


os.environ["OPENAI_API_KEY"] = config("OPENAI_API_KEY")
PERSIST_DIR = "onerb_db"

def load_data_from_database(season: int, limite: int = 100):
    db = SessionLocal()
    try:
        query = db.query(Game).filter(Game.season == season).order_by(Game.date_start)
        jogos = query.limit(limite).all()

        documentos = []

        for jogo in jogos:
            time_casa = db.query(Team).filter(Team.id == jogo.home_team_id).first()
            time_fora = db.query(Team).filter(Team.id == jogo.away_team_id).first()

            placar_casa = db.query(GameTeamScore).filter(
                GameTeamScore.game_id == jogo.id,
                GameTeamScore.is_home == True,
            ).first()

            placar_fora = db.query(GameTeamScore).filter(
                GameTeamScore.game_id == jogo.id,
                GameTeamScore.is_home == False,
            ).first()

            nome_casa = time_casa.name if time_casa else "Time da Casa"
            nome_fora = time_fora.name if time_fora else "Time Visitante"

            pontos_casa = placar_casa.points if placar_casa and placar_casa.points else 0
            pontos_fora = placar_fora.points if placar_fora and placar_fora.points else 0

            if jogo.date_start:
                data_str = jogo.date_start.strftime("%d/%m/%Y")
            else:
                data_str = "Data desconhecida"

            texto = f"""
            Temporada: {jogo.season}
            Data: {data_str}
            Time da casa: {nome_casa}
            Time visitante: {nome_fora}
            Placar final: {nome_casa} {pontos_casa} x {pontos_fora} {nome_fora}
            Status: {jogo.status_long or 'N/A'}
            """

            documento = Document(page_content=texto.strip(),
                metadata={
                    "game_id": jogo.id,
                    "season": jogo.season,
                    "home_team": nome_casa,
                    "away_team": nome_fora,
                },
            )
            documentos.append(documento)

        return documentos
    finally:
        db.close()

def docs_chunks(docs):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=200,
    )
    chunks = text_splitter.split_documents(docs)
    return chunks

def load_vector_store():
    if os.path.exists(PERSIST_DIR):
        vector_store = Chroma(
            persist_directory=PERSIST_DIR,
            embedding_function=OpenAIEmbeddings(),
        )
        return vector_store
    return None

def create_vector_store(chunks):
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=OpenAIEmbeddings(),
        persist_directory=PERSIST_DIR,
    )
    return vector_store

def ask_question(modelo, query, vector_store):
    llm = ChatOpenAI(model=modelo, temperature=1.0)
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})

    system_prompt = """
    Você é o Onerb, um assistente especializado exclusivamente em responder perguntas sobre jogos da NBA com base APENAS no contexto fornecido.
    O contexto contém informações estruturadas sobre partidas da NBA, incluindo:
    - Times
    - Placar
    - Data
    - Status do jogo (finalizado, ao vivo, agendado, etc.)

    REGRAS OBRIGATÓRIAS:
    1. Utilize SOMENTE as informações presentes no contexto.
    2. NUNCA faça suposições, inferências ou use conhecimento externo.
    3. Se a informação solicitada NÃO estiver claramente presente no contexto, responda exatamente: "Não encontrei essa informação no contexto."
    4. Responda SEMPRE em português.
    5. Seja direto, claro e objetivo.
    6. Utilize formatação em Markdown sempre que fizer sentido:
       - **Negrito** para destaques
       - Listas para múltiplos jogos ou informações
    CONTEXTO: {context}
    """

    mensagens = [("system", system_prompt)]
    for msg in st.session_state.messages:
        mensagens.append((msg["role"], msg["content"]))
    mensagens.append(("human", "{input}"))

    prompt = ChatPromptTemplate.from_messages(mensagens)

    qa_chain = create_stuff_documents_chain(
        llm=llm,
        prompt=prompt,
    )

    chain = create_retrieval_chain(
        retriever=retriever,
        combine_docs_chain=qa_chain,
    )

    resposta = chain.invoke({"input": query})
    return resposta.get("answer")

st.set_page_config(
    page_title="Onerb",
    page_icon="🏀",
)

st.title("🏀 Onerb")

with st.sidebar:
    st.header("Configurações")
    temp = st.number_input(
        "Temporada (ano)",
        min_value=2015,
        max_value=2024,
        value=2021,
        step=1,
    )

    limit = st.number_input(
        "Quantidade de jogos para carregar",
        min_value=10,
        max_value=500,
        value=100,
        step=10,
    )

    if st.button("Carregar/atualizar dados do banco"):
        with st.spinner("Carregando jogos do banco..."):
            docs = load_data_from_database(season=temp, limite=limit)
            chunks = docs_chunks(docs)
            vs = create_vector_store(chunks)
            st.session_state["vector_store"] = vs
            st.success(f"{len(docs)} jogos carregados e indexados!")

    st.markdown("---")

    models = [
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-4-turbo",
        "gpt-3.5-turbo",
    ]
    selected_model = st.selectbox("Modelo LLM", models)

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "vector_store" not in st.session_state:
    vs = load_vector_store()
    if vs:
        st.session_state["vector_store"] = vs

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

query = st.chat_input("Faça uma pergunta sobre jogos da NBA...")

if query:
    if "vector_store" not in st.session_state:
        st.error("Você precisa carregar os dados primeiro na barra lateral.")
    else:
        st.session_state["messages"].append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        with st.chat_message("assistant"):
            with st.spinner("Consultando..."):
                resposta = ask_question(
                    modelo=selected_model,
                    query=query,
                    vector_store=st.session_state["vector_store"],
                )
                st.markdown(resposta)