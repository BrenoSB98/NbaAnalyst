import logging
import os
import time
import unicodedata
from datetime import datetime

from prompts import (
    MESES_PT,
    PADROES_ENRIQUECIMENTO_WEB,
    DOMINIOS_CONFIAVEIS,
    PALAVRAS_NOTICIAS_AMPLAS,
)

logger = logging.getLogger("web_search")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")


def _normalizar(texto):
    nfkd = unicodedata.normalize("NFKD", str(texto))
    sem_acento = "".join(c for c in nfkd if not unicodedata.combining(c))
    return sem_acento.lower()


def _enriquecer_query(pergunta):
    pergunta_norm = _normalizar(pergunta)
    termo_extra = None
    for padrao in PADROES_ENRIQUECIMENTO_WEB:
        for palavra in padrao["palavras"]:
            if palavra in pergunta_norm:
                termo_extra = padrao["termos"]
                break
        if termo_extra:
            break
    base = pergunta
    if "nba" not in pergunta_norm and "basquete" not in pergunta_norm:
        base = pergunta + " NBA"
    hoje = datetime.now()
    data_str = f"{hoje.day} {MESES_PT[hoje.month]} {hoje.year}"
    if termo_extra:
        return base + " " + termo_extra + " " + data_str
    return base + " " + data_str


def _eh_pergunta_complexa(pergunta):
    pergunta_norm = _normalizar(pergunta)
    indicadores = [
        "lista",
        "liste",
        "top 10",
        "top 5",
        "ultimos 5",
        "ultimas 5",
        "ultimos 3",
        "ultimas 3",
        "ultimos 10",
        "ultimas 10",
        "compare",
        "comparar",
        "diferenca entre",
        "historico",
        "historia",
    ]
    for ind in indicadores:
        if ind in pergunta_norm:
            return True
    return False


def _eh_pergunta_de_noticia(pergunta):
    pergunta_norm = _normalizar(pergunta)
    for palavra in PALAVRAS_NOTICIAS_AMPLAS:
        if palavra in pergunta_norm:
            return True
    return False


def buscar_na_web(pergunta):
    if not TAVILY_API_KEY:
        logger.warning("web_search: TAVILY_API_KEY não configurada")
        return ""
    inicio = time.time()
    try:
        from langchain_tavily import TavilySearch

        query = _enriquecer_query(pergunta)
        complexa = _eh_pergunta_complexa(pergunta)
        noticia = _eh_pergunta_de_noticia(pergunta)

        if complexa and not noticia:
            max_resultados = 4
            search_depth = "advanced"
            include_domains = DOMINIOS_CONFIAVEIS
        elif noticia:
            max_resultados = 4
            search_depth = "basic"
            include_domains = None
        else:
            max_resultados = 3
            search_depth = "basic"
            include_domains = DOMINIOS_CONFIAVEIS

        logger.warning(
            f"web_search: query={query!r}, complexa={complexa}, noticia={noticia}, depth={search_depth}, domains={include_domains}"
        )

        params = {
            "max_results": max_resultados,
            "topic": "general",
            "include_answer": True,
            "search_depth": search_depth,
        }
        if include_domains:
            params["include_domains"] = include_domains

        ferramenta = TavilySearch(**params)
        resultados = ferramenta.invoke(query)

        partes = []
        answer = ""
        if isinstance(resultados, dict):
            answer = resultados.get("answer", "") or ""
            if answer:
                partes.append(answer)
            if complexa or not answer:
                for r in resultados.get("results", []):
                    titulo = r.get("title", "")
                    conteudo = r.get("content", "")
                    if titulo and conteudo:
                        partes.append(titulo + ": " + conteudo[:400])
        elif isinstance(resultados, list):
            for r in resultados:
                if isinstance(r, dict):
                    titulo = r.get("title", "")
                    conteudo = r.get("content", "")
                    if titulo and conteudo:
                        partes.append(titulo + ": " + conteudo[:400])
                elif isinstance(r, str):
                    partes.append(r)
        elif isinstance(resultados, str):
            partes.append(resultados)
        else:
            partes.append(str(resultados))

        contexto = "\n\n".join(partes)
        tempo = time.time() - inicio
        logger.warning(
            f"web_search: {len(contexto)} chars, answer_only={bool(answer and not complexa)}, tempo={tempo:.2f}s"
        )
        return contexto
    except ImportError:
        logger.error("web_search: langchain-tavily não instalado")
        return ""
    except Exception as erro:
        logger.error(f"web_search: erro na busca: {erro}")
        return ""
