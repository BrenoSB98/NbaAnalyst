import os
import logging

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document

from conhecimento_nba import DOCUMENTOS_CONHECIMENTO

logger = logging.getLogger(__name__)

PASTA_CHROMA = os.path.join(os.path.dirname(__file__), "chroma_db")
COLECAO_NOME = "conhecimento_nba"

_vectorstore = None

def _criar_documentos():
    docs = []
    for item in DOCUMENTOS_CONHECIMENTO:
        doc = Document(
            page_content=item["titulo"] + "\n\n" + item["conteudo"].strip(),
            metadata={"id": item["id"], "titulo": item["titulo"]}
        )
        docs.append(doc)
    return docs

def inicializar_base_conhecimento():
    global _vectorstore

    if _vectorstore is not None:
        return _vectorstore

    chave_openai = os.getenv("OPENAI_API_KEY", "")
    if not chave_openai:
        logger.warning("OPENAI_API_KEY ausente — base de conhecimento desativada.")
        return None

    try:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        if os.path.exists(PASTA_CHROMA):
            logger.info("Carregando base de conhecimento existente...")
            _vectorstore = Chroma(collection_name=COLECAO_NOME, embedding_function=embeddings, persist_directory=PASTA_CHROMA)
            logger.info("Base de conhecimento carregada.")
        else:
            logger.info("Criando base de conhecimento pela primeira vez...")
            os.makedirs(PASTA_CHROMA, exist_ok=True)
            docs = _criar_documentos()
            _vectorstore = Chroma.from_documents(
                documents=docs,
                embedding=embeddings,
                collection_name=COLECAO_NOME,
                persist_directory=PASTA_CHROMA
            )
            logger.info(f"Base criada com {len(docs)} documentos.")

        return _vectorstore

    except Exception as erro:
        logger.error(f"Erro ao inicializar base de conhecimento: {erro}")
        return None

def reindexar_base_conhecimento():
    global _vectorstore

    chave_openai = os.getenv("OPENAI_API_KEY", "")
    if not chave_openai:
        logger.warning("OPENAI_API_KEY ausente — reindexação cancelada.")
        return False

    try:
        import shutil
        if os.path.exists(PASTA_CHROMA):
            shutil.rmtree(PASTA_CHROMA)
            logger.info("Base antiga removida.")

        _vectorstore = None
        inicializar_base_conhecimento()
        logger.info("Reindexação concluída.")
        return True

    except Exception as erro:
        logger.error(f"Erro ao reindexar: {erro}")
        return False

def buscar_na_base_conhecimento(pergunta, n_resultados=3):
    vectorstore = inicializar_base_conhecimento()

    if vectorstore is None:
        return ""

    try:
        resultados = vectorstore.similarity_search(pergunta, k=n_resultados)

        if not resultados:
            return ""

        partes = []
        for doc in resultados:
            partes.append(doc.page_content)

        return "\n\n---\n\n".join(partes)

    except Exception as erro:
        logger.error(f"Erro ao buscar na base de conhecimento: {erro}")
        return ""