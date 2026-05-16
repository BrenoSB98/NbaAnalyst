import logging
import re
from typing import List

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import Field

from conhecimento_nba import DOCUMENTOS_CONHECIMENTO

logger = logging.getLogger(__name__)

_STOPWORDS = {
    "o", "a", "os", "as", "um", "uma", "de", "do", "da", "dos", "das",
    "em", "no", "na", "nos", "nas", "ao", "aos", "por", "para", "com",
    "que", "se", "e", "ou", "mas", "não", "mais", "como", "quando",
    "onde", "quem", "qual", "quais", "quanto", "sobre", "entre",
    "nba", "jogo", "jogos", "time", "times", "jogador", "ser", "ter",
    "foi", "tem", "são", "está", "faz", "fez", "isso", "isso",
}

_documentos_cache = None

def _preparar_documentos():
    global _documentos_cache
    if _documentos_cache is not None:
        return _documentos_cache
    docs = []
    for item in DOCUMENTOS_CONHECIMENTO:
        conteudo = item["titulo"] + "\n\n" + item["conteudo"].strip()
        doc = Document(page_content=conteudo, metadata={"id": item["id"], "titulo": item["titulo"]})
        docs.append(doc)
    _documentos_cache = docs
    logger.info(f"Base de conhecimento: {len(docs)} documentos preparados")
    return docs

def _tokenizar(texto):
    texto_limpo = texto.lower()
    texto_limpo = re.sub(r"[^\w\s]", " ", texto_limpo)
    palavras = texto_limpo.split()
    tokens = []
    for p in palavras:
        if len(p) > 2 and p not in _STOPWORDS:
            tokens.append(p)
    return tokens

def _pontuar_documento(doc, tokens_pergunta):
    texto = doc.page_content.lower()
    titulo = doc.metadata.get("titulo", "").lower()
    pontuacao = 0

    for token in tokens_pergunta:
        if token in titulo:
            pontuacao = pontuacao + 3
        contagem = texto.count(token)
        if contagem > 0:
            pontuacao = pontuacao + min(contagem, 4)

    return pontuacao

class RetrieverKeyword(BaseRetriever):
    n_resultados: int = Field(default=2)

    def _get_relevant_documents(self, query: str, **kwargs) -> List[Document]:
        docs = _preparar_documentos()
        tokens = _tokenizar(query)
        if not tokens:
            return []
        scores = []
        for doc in docs:
            pontuacao = _pontuar_documento(doc, tokens)
            if pontuacao > 0:
                scores.append((pontuacao, doc))
        scores.sort(key=lambda x: x[0], reverse=True)
        resultado = []
        for i in range(min(self.n_resultados, len(scores))):
            resultado.append(scores[i][1])
        return resultado

def obter_retriever(n_resultados=2):
    return RetrieverKeyword(n_resultados=n_resultados)

def buscar_na_base_conhecimento(pergunta, n_resultados=2):
    retriever = obter_retriever(n_resultados)
    try:
        docs = retriever.invoke(pergunta)
        partes = []
        for doc in docs:
            partes.append(doc.page_content)
        return "\n\n---\n\n".join(partes)
    except Exception as erro:
        logger.error(f"Erro na busca de conhecimento: {erro}")
        return ""

def inicializar_base_conhecimento():
    _preparar_documentos()
    return True

def reindexar_base_conhecimento():
    global _documentos_cache
    _documentos_cache = None
    _preparar_documentos()
    return True