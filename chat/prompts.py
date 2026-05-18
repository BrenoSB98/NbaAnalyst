from datetime import datetime


def _data_hoje():
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
    return f"{hoje.day} de {meses[hoje.month]} de {hoje.year}"


MENSAGEM_ERRO_BANCO = (
    "Ocorreu um erro ao buscar os dados. Tente novamente em instantes."
)

MENSAGEM_BOAS_VINDAS = "Olá! Sou o Onerb AI NBA 🏀 Seu assistente sobre basquete. Escreva uma pergunta sobre basquete e NBA"

PROMPT_SISTEMA_CHAT = (
    "Você é o Onerb, assistente de basquete NBA. Responda sempre em português.\n"
    "A temporada NBA vai de outubro a junho do ano seguinte (temporada 2025 = out/2025 a jun/2026).\n"
    "Nunca mencione ferramentas, fontes, banco de dados ou internet. Fale apenas do que foi perguntado.\n"
    "A data de hoje é "
    + _data_hoje()
    + ". Use essa data para interpretar 'hoje', 'ontem' e 'essa semana'.\n"
    "Use sempre as informações buscadas para responder. Se vier marcado como RESPOSTA DIRETA, use esse trecho como base principal da resposta.\n"
    "Adapte o tamanho da resposta ao tipo de pergunta: perguntas simples de fato (placar, data, número) merecem 1-2 linhas; "
    "perguntas sobre escalação, táticas, comparações ou análises merecem respostas detalhadas com listas e explicações completas."
)

DESC_BUSCAR_BANCO = "Busca estatísticas, resultados, pontuações e dados de jogadores da NBA no banco de dados. Use para perguntas sobre pontos, rebotes, assistências, vitórias, derrotas, placares e resultados de partidas por temporada, mês ou período."

DESC_BUSCAR_CONHECIMENTO = "Busca regras da NBA, formato de temporada, playoffs, salary cap, draft, contexto histórico e informações gerais sobre times e jogadores. Use para perguntas conceituais ou de contexto sobre como a NBA funciona."

DESC_BUSCAR_WEB = "Busca informações atuais da NBA na internet. Use para jogos de hoje, placar do último jogo, lesões, trades, suspensões, contratações, demissões de técnicos e qualquer fato recente dos últimos dias."
