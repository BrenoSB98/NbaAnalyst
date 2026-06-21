from datetime import datetime

MESES_PT = {
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


def _data_hoje():
    hoje = datetime.now()
    return f"{hoje.day} de {MESES_PT[hoje.month]} de {hoje.year}"


DOMINIOS_CONFIAVEIS = [
    "wikipedia.org",
    "nba.com",
    "basketball-reference.com",
    "espn.com",
    "sofascore.com",
    "flashscore.com",
    "r10score.com",
    "globoesporte.globo.com",
]

PALAVRAS_NOTICIAS_AMPLAS = [
    "hoje",
    "ontem",
    "lesao",
    "lesionado",
    "lesoes",
    "machucado",
    "trade",
    "transferencia",
    "negociacao",
    "demitido",
    "demissao",
    "contratado",
    "contratacao",
    "assinou",
    "renovacao",
]

MENSAGEM_ERRO_BANCO = (
    "Ocorreu um erro ao buscar os dados. Tente novamente em instantes."
)

MENSAGEM_BOAS_VINDAS = (
    "Olá! Sou o Onerb AI NBA. Escreva uma pergunta sobre basquete e NBA"
)

MENSAGEM_FORA_ESCOPO_APOSTAS = "Não respondo perguntas sobre apostas. Sou um assistente focado em estatísticas, jogos, jogadores e informações sobre a NBA."

PROMPT_SISTEMA_CHAT = (
    "Você é o Onerb, assistente de basquete NBA. Responda em português, de forma natural e conversacional.\n"
    "Temporada NBA vai de outubro a junho. Temporada 2025 = out/2025 a jun/2026. Hoje é "
    + _data_hoje()
    + ".\n"
    "Apostas, odds, fantasy estão fora do escopo. Para apostas, responda: 'Não respondo perguntas sobre apostas.'\n"
    "\n"
    "Escolha da ferramenta:\n"
    "- Use o BANCO para perguntas estruturadas com dados específicos E COM TEMPORADA EXPLÍCITA NA PERGUNTA. Exemplos: 'média de pontos do Curry na temporada 2025', 'todos os jogos do Lakers em março de 2025', 'classificação completa do Oeste em 2024', 'top 10 em rebotes em 2024', 'compare Curry e LeBron em 2024'.\n"
    "- Use a WEB para perguntas sobre dados recentes ou sem temporada explícita. Exemplos: 'últimos 10 jogos dos Lakers', 'jogos do Celtics essa semana', 'cestinha da liga atualmente', 'atual campeão', 'MVP', 'Rookie of the Year', 'prêmios', 'lesões', 'trades', 'jogos de hoje', 'último resultado', 'placares de finais', 'escalações', 'comparações qualitativas' ('o LeBron é o melhor de todos os tempos?'), 'recordes recentes'.\n"
    "- Use o CONHECIMENTO para perguntas sobre regras, formato dos playoffs, táticas (pick and roll, spacing), analytics (PER, TS%, BPM) e dinastias históricas.\n"
    "- Se uma ferramenta do banco responder 'dados incompletos' ou 'use buscar_web', chame imediatamente buscar_web. Não tente usar os dados parciais.\n"
    "Quando a ferramenta retornar a informação solicitada, responda imediatamente sem chamar mais ferramentas.\n"
    "Quando a pergunta pedir informações sobre vários itens distintos (ex: 'placares de cada uma das 5 finais', 'stats do Curry e do LeBron'), faça TODAS as chamadas necessárias em PARALELO no mesmo round, não uma por vez.\n"
    "\n"
    "Use apenas os dados retornados pelas ferramentas. NUNCA invente fatos, datas, nomes ou números a partir da sua memória.\n"
    "Se pediram uma lista de N itens e os dados retornados só contêm M (com M < N), liste os M que você tem e diga: 'não encontrei os outros'. NÃO complete a lista chutando os anos/nomes que faltam.\n"
    "Se a informação simplesmente não está nos dados, diga 'não encontrei essa informação' e pare.\n"
    "\n"
    "Não use markdown na resposta. Sem asteriscos para negrito, sem hashtags para títulos. Use texto puro.\n"
    "Adapte o tamanho: fatos pontuais merecem 2-3 frases com contexto; listas e comparações merecem respostas estruturadas em linhas separadas.\n"
    "Nunca mencione ferramentas, fontes ou banco de dados ao usuário."
)

DESC_STATS_JOGADOR = "Estatísticas de um jogador em uma temporada (média de pontos, rebotes, assistências, etc). Parâmetros: nome do jogador e temporada (ano)."

DESC_JOGOS_TIME = "Jogos e placares de um time em um mês/ano ou em uma temporada. Parâmetros: nome do time, ano e (opcional) mês."

DESC_LIDERES_LIGA = "Líderes da liga em uma estatística (pontos, rebotes, assistências, roubos, tocos) para uma temporada. Use TAMBÉM para 'cestinha', 'maior pontuador', 'maior assistente', 'maior reboteiro', 'rei dos tocos', 'rei dos roubos'. Parâmetros: estatística e temporada."

DESC_COMPARAR_JOGADORES = "Compara estatísticas de jogadores na mesma temporada. Parâmetros: lista de nomes e temporada."

DESC_CLASSIFICACAO = "Classificação dos times em uma temporada. Parâmetros: conferência (Leste, Oeste ou todas) e temporada."

DESC_BUSCAR_CONHECIMENTO = "Informações conceituais sobre a NBA: regras, posições, formato dos playoffs, draft, salary cap, táticas, analytics, perfis históricos, recordes. NÃO use para campeão, MVP ou stats atuais."

DESC_BUSCAR_WEB = "Busca informações da NBA na internet em fontes como Wikipedia, NBA.com, Basketball-Reference, ESPN, Sofascore, Flashscore e Globo Esporte. Use para: atual campeão, MVP, cestinha, prêmios, jogos de hoje, último resultado, placares de finais, lesões, trades, escalações, comparações qualitativas e fatos recentes."

PADROES_ENRIQUECIMENTO_WEB = [
    {
        "palavras": ["finals mvp", "mvp das finais", "mvp dos playoffs"],
        "termos": "NBA Finals MVP award",
    },
    {
        "palavras": [
            "placar das finais",
            "placares das finais",
            "placar da final",
            "placares da final",
            "placares das ultimas",
            "placares dos jogos",
            "placares de cada partida",
            "placares de cada jogo",
            "game by game",
            "jogo a jogo",
        ],
        "termos": "NBA Finals game scores results",
    },
    {
        "palavras": [
            "campeao",
            "campeoes",
            "campea",
            "campeas",
            "vencedor das finais",
            "ganhou as finais",
        ],
        "termos": "NBA Finals champion winner",
    },
    {"palavras": ["mvp"], "termos": "NBA MVP regular season award"},
    {
        "palavras": ["rookie of the year", "rookie do ano", "calouro do ano"],
        "termos": "NBA Rookie of the Year",
    },
    {
        "palavras": ["dpoy", "defensive player", "melhor defensor"],
        "termos": "NBA Defensive Player of the Year",
    },
    {"palavras": ["draft"], "termos": "NBA draft first pick"},
    {
        "palavras": ["lesao", "lesionado", "lesoes", "machucado", "injury"],
        "termos": "NBA injury report",
    },
    {"palavras": ["trade", "transferencia", "negociacao"], "termos": "NBA trade deal"},
    {
        "palavras": [
            "jogo de hoje",
            "jogos de hoje",
            "jogos hoje",
            "tem hoje",
            "jogo de ontem",
            "jogos de ontem",
            "ultimo jogo",
            "ultima partida",
        ],
        "termos": "NBA games schedule today scoreboard",
    },
    {
        "palavras": ["escalacao", "starting five", "time titular", "provavel titular"],
        "termos": "NBA starting lineup projected",
    },
    {"palavras": ["classificacao", "standings", "tabela"], "termos": "NBA standings"},
]
