import logging
import os
import time
from datetime import datetime

logger = logging.getLogger("web_search")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")


def _query_com_data(pergunta):
    meses = {
        1: "janeiro",
        2: "fevereiro",
        3: "março",
        4: "abril",
        5: "maio",
        6: "junho",
        7: "julho",
        8: "agosto",
        9: "setembro",
        10: "outubro",
        11: "novembro",
        12: "dezembro",
    }
    hoje = datetime.now()
    data_str = f"{hoje.day} {meses[hoje.month]} {hoje.year}"
    query = pergunta
    if "nba" not in pergunta.lower() and "basquete" not in pergunta.lower():
        query = pergunta + " NBA"
    query = query + " " + data_str
    return query


def buscar_na_web(pergunta, max_resultados=4):
    if not TAVILY_API_KEY:
        logger.warning("web_search: TAVILY_API_KEY não configurada")
        return ""
    inicio = time.time()
    try:
        from langchain_tavily import TavilySearch

        query = _query_com_data(pergunta)
        logger.warning(f"web_search: query={query!r}")
        ferramenta = TavilySearch(
            max_results=max_resultados, topic="general", include_answer=True
        )
        resultados = ferramenta.invoke(query)
        partes = []
        if isinstance(resultados, dict):
            resposta_direta = resultados.get("answer", "")
            if resposta_direta:
                partes.append("RESPOSTA DIRETA: " + resposta_direta)
            for r in resultados.get("results", []):
                titulo = r.get("title", "")
                conteudo = r.get("content", "")
                if titulo and conteudo:
                    partes.append(titulo + ": " + conteudo)
        elif isinstance(resultados, list):
            for r in resultados:
                if isinstance(r, dict):
                    titulo = r.get("title", "")
                    conteudo = r.get("content", "")
                    if titulo and conteudo:
                        partes.append(titulo + ": " + conteudo)
                elif isinstance(r, str):
                    partes.append(r)
        elif isinstance(resultados, str):
            partes.append(resultados)
        else:
            partes.append(str(resultados))
        contexto = "\n---\n".join(partes)
        tempo = time.time() - inicio
        logger.warning(
            f"web_search: {len(contexto)} chars, tempo={tempo:.2f}s, preview={contexto[:200]!r}"
        )
        return contexto
    except ImportError:
        logger.error("web_search: langchain-tavily não instalado")
        return ""
    except Exception as erro:
        logger.error(f"web_search: erro na busca: {erro}")
        return ""
