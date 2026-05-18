import logging
import os
import time

from sqlalchemy import create_engine, text

logger = logging.getLogger("db_chat")

_user = os.getenv("POSTGRES_USER")
_password = os.getenv("POSTGRES_PASSWORD")
_host = os.getenv("POSTGRES_HOST", "postgres")
_port = os.getenv("POSTGRES_PORT", "5432")
_db = os.getenv("POSTGRES_DB")

DATABASE_URL = f"postgresql://{_user}:{_password}@{_host}:{_port}/{_db}"
logger.warning(f"db_chat: DATABASE_URL host={_host}, db={_db}, user={_user}")

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5)

_APELIDOS_TIMES = {
    "lakers": "Los Angeles Lakers",
    "celtics": "Boston Celtics",
    "warriors": "Golden State Warriors",
    "bulls": "Chicago Bulls",
    "heat": "Miami Heat",
    "nets": "Brooklyn Nets",
    "knicks": "New York Knicks",
    "bucks": "Milwaukee Bucks",
    "suns": "Phoenix Suns",
    "clippers": "LA Clippers",
    "nuggets": "Denver Nuggets",
    "mavericks": "Dallas Mavericks",
    "mavs": "Dallas Mavericks",
    "dallas": "Dallas Mavericks",
    "76ers": "Philadelphia 76ers",
    "sixers": "Philadelphia 76ers",
    "philadelphia": "Philadelphia 76ers",
    "raptors": "Toronto Raptors",
    "toronto": "Toronto Raptors",
    "spurs": "San Antonio Spurs",
    "san antonio": "San Antonio Spurs",
    "thunder": "Oklahoma City Thunder",
    "okc": "Oklahoma City Thunder",
    "oklahoma": "Oklahoma City Thunder",
    "jazz": "Utah Jazz",
    "utah": "Utah Jazz",
    "rockets": "Houston Rockets",
    "houston": "Houston Rockets",
    "pistons": "Detroit Pistons",
    "detroit": "Detroit Pistons",
    "hawks": "Atlanta Hawks",
    "atlanta": "Atlanta Hawks",
    "hornets": "Charlotte Hornets",
    "charlotte": "Charlotte Hornets",
    "pacers": "Indiana Pacers",
    "indiana": "Indiana Pacers",
    "magic": "Orlando Magic",
    "orlando": "Orlando Magic",
    "wizards": "Washington Wizards",
    "washington": "Washington Wizards",
    "cavaliers": "Cleveland Cavaliers",
    "cavs": "Cleveland Cavaliers",
    "cleveland": "Cleveland Cavaliers",
    "timberwolves": "Minnesota Timberwolves",
    "wolves": "Minnesota Timberwolves",
    "minnesota": "Minnesota Timberwolves",
    "grizzlies": "Memphis Grizzlies",
    "memphis": "Memphis Grizzlies",
    "pelicans": "New Orleans Pelicans",
    "new orleans": "New Orleans Pelicans",
    "kings": "Sacramento Kings",
    "sacramento": "Sacramento Kings",
    "trail blazers": "Portland Trail Blazers",
    "blazers": "Portland Trail Blazers",
    "portland": "Portland Trail Blazers",
    "denver": "Denver Nuggets",
    "boston": "Boston Celtics",
    "golden state": "Golden State Warriors",
    "chicago": "Chicago Bulls",
    "miami": "Miami Heat",
    "brooklyn": "Brooklyn Nets",
    "new york": "New York Knicks",
    "milwaukee": "Milwaukee Bucks",
    "phoenix": "Phoenix Suns",
    "los angeles lakers": "Los Angeles Lakers",
    "la clippers": "LA Clippers",
    "los angeles clippers": "LA Clippers",
}

_PALAVRAS_IGNORAR = {
    "jogador",
    "atleta",
    "player",
    "stats",
    "estatistica",
    "pontos",
    "assistencia",
    "rebote",
    "temporada",
    "jogo",
    "partida",
    "resultado",
    "placar",
    "time",
    "franquia",
    "equipe",
    "nba",
    "qual",
    "quais",
    "como",
    "quando",
    "onde",
    "quantos",
    "quantas",
    "teve",
    "fez",
    "media",
    "total",
    "melhor",
    "pior",
    "mais",
    "menos",
    "voce",
    "para",
    "qual",
    "esse",
    "esta",
    "esse",
    "isso",
    "pelo",
    "pela",
    "numa",
    "com",
    "sem",
    "por",
    "titulo",
    "titulos",
    "sobre",
    "jogou",
    "joga",
    "faz",
    "marca",
    "teve",
    "seus",
    "suas",
    "este",
    "aquele",
    "tem",
    "ter",
    "ser",
    "sido",
    "resultados",
    "foram",
}

_MESES_PT = {
    "janeiro": 1,
    "fevereiro": 2,
    "março": 3,
    "marco": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
    "jan": 1,
    "fev": 2,
    "mar": 3,
    "abr": 4,
    "mai": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "set": 9,
    "out": 10,
    "nov": 11,
    "dez": 12,
}

_PALAVRAS_NAO_NOME = (
    set(_APELIDOS_TIMES.keys())
    | set(_MESES_PT.keys())
    | {"2020", "2021", "2022", "2023", "2024", "2025", "2026", "2027"}
)

_cache_temporadas = {"valor": None, "ts": 0}


def _extrair_possiveis_times(texto):
    encontrados = []
    for apelido in _APELIDOS_TIMES:
        if apelido in texto:
            encontrados.append(apelido)
    return encontrados


def _extrair_possiveis_nomes(texto):
    palavras_validas = []
    for palavra in texto.split():
        palavra_limpa = palavra.strip("?.,!:;()\"'").lower()
        if (
            len(palavra_limpa) > 2
            and palavra_limpa not in _PALAVRAS_IGNORAR
            and palavra_limpa not in _PALAVRAS_NAO_NOME
        ):
            palavras_validas.append(palavra_limpa)
    if not palavras_validas:
        return []
    bigrams = []
    for i in range(len(palavras_validas) - 1):
        bigrams.append(palavras_validas[i] + " " + palavras_validas[i + 1])
    if bigrams:
        return bigrams
    return palavras_validas


def _extrair_temporadas(texto):
    temporadas = []
    for ano in range(2010, 2027):
        if str(ano) in texto:
            temporadas.append(ano)
    return temporadas


def _extrair_mes_ano(texto):
    texto_lower = texto.lower()
    for nome_mes, num_mes in _MESES_PT.items():
        if nome_mes in texto_lower:
            for ano in range(2020, 2028):
                if str(ano) in texto_lower:
                    return num_mes, ano
    return None, None


def buscar_jogador_por_nome(nome):
    try:
        partes = nome.strip().split()
        with engine.connect() as conn:
            if len(partes) >= 2:
                linhas = conn.execute(
                    text(
                        "SELECT firstname, lastname, birth_country, nba_start FROM players WHERE (firstname ILIKE :p AND lastname ILIKE :u) OR (firstname ILIKE :u AND lastname ILIKE :p) LIMIT 2"
                    ),
                    {"p": f"%{partes[0]}%", "u": f"%{partes[1]}%"},
                ).fetchall()
            else:
                linhas = conn.execute(
                    text(
                        "SELECT firstname, lastname, birth_country, nba_start FROM players WHERE lastname ILIKE :t LIMIT 2"
                    ),
                    {"t": f"%{nome}%"},
                ).fetchall()
        if not linhas:
            return ""
        saida = []
        for l in linhas:  # noqa: E741
            saida.append(
                f"- {l.firstname} {l.lastname} | {l.birth_country} | NBA desde {l.nba_start}"
            )
        return "\n".join(saida)
    except Exception as e:
        logger.error(f"Erro buscar_jogador_por_nome: {e}")
        return ""


def buscar_stats_jogador_na_temporada(nome_jogador, temporada):
    try:
        partes = nome_jogador.strip().split()
        with engine.connect() as conn:
            if len(partes) >= 2:
                jogadores = conn.execute(
                    text(
                        "SELECT id, firstname, lastname FROM players WHERE (firstname ILIKE :p AND lastname ILIKE :u) OR (firstname ILIKE :u AND lastname ILIKE :p) LIMIT 2"
                    ),
                    {"p": f"%{partes[0]}%", "u": f"%{partes[1]}%"},
                ).fetchall()
            else:
                jogadores = conn.execute(
                    text(
                        "SELECT id, firstname, lastname FROM players WHERE lastname ILIKE :t LIMIT 2"
                    ),
                    {"t": f"%{nome_jogador}%"},
                ).fetchall()
        if not jogadores:
            return ""
        saida = []
        for jogador in jogadores:
            with engine.connect() as conn:
                row = conn.execute(
                    text(
                        "SELECT COUNT(*) AS jogos, ROUND(AVG(points)::numeric, 1) AS pts, ROUND(AVG(assists)::numeric, 1) AS ast, ROUND(AVG(tot_reb)::numeric, 1) AS reb, ROUND(AVG(steals)::numeric, 1) AS stl, ROUND(AVG(blocks)::numeric, 1) AS blk, ROUND(AVG(turnovers)::numeric, 1) AS tov FROM player_game_stats WHERE player_id = :pid AND season = :t"
                    ),
                    {"pid": jogador.id, "t": temporada},
                ).fetchone()
            if not row or row.jogos == 0:
                continue
            saida.append(
                f"{jogador.firstname} {jogador.lastname} | Temp {temporada} | {row.jogos} jogos | Pts: {row.pts} | Ast: {row.ast} | Reb: {row.reb} | Stl: {row.stl} | Blk: {row.blk}"
            )
        return "\n".join(saida)
    except Exception as e:
        logger.error(f"Erro buscar_stats_jogador_na_temporada: {e}")
        return ""


def buscar_stats_recentes_jogador(nome_jogador):
    try:
        partes = nome_jogador.strip().split()
        with engine.connect() as conn:
            if len(partes) >= 2:
                jogadores = conn.execute(
                    text(
                        "SELECT id, firstname, lastname FROM players WHERE (firstname ILIKE :p AND lastname ILIKE :u) OR (firstname ILIKE :u AND lastname ILIKE :p) LIMIT 2"
                    ),
                    {"p": f"%{partes[0]}%", "u": f"%{partes[1]}%"},
                ).fetchall()
            else:
                jogadores = conn.execute(
                    text(
                        "SELECT id, firstname, lastname FROM players WHERE lastname ILIKE :t LIMIT 2"
                    ),
                    {"t": f"%{nome_jogador}%"},
                ).fetchall()
        if not jogadores:
            return ""
        saida = []
        for jogador in jogadores:
            with engine.connect() as conn:
                row = conn.execute(
                    text(
                        "SELECT COUNT(*) AS jogos, ROUND(AVG(pgs.points)::numeric, 1) AS pts, ROUND(AVG(pgs.assists)::numeric, 1) AS ast, ROUND(AVG(pgs.tot_reb)::numeric, 1) AS reb, MAX(g.season) AS temporada FROM player_game_stats pgs JOIN games g ON g.id = pgs.game_id WHERE pgs.player_id = :pid AND g.status_short = 3 AND g.date_start >= (SELECT MAX(g2.date_start) - INTERVAL '30 days' FROM games g2 JOIN player_game_stats p2 ON p2.game_id = g2.id WHERE p2.player_id = :pid AND g2.status_short = 3)"
                    ),
                    {"pid": jogador.id},
                ).fetchone()
            if not row or row.jogos == 0:
                continue
            saida.append(
                f"{jogador.firstname} {jogador.lastname} | Últimos {row.jogos} jogos (temp. {row.temporada}) | Pts: {row.pts} | Ast: {row.ast} | Reb: {row.reb}"
            )
        return "\n".join(saida)
    except Exception as e:
        logger.error(f"Erro buscar_stats_recentes_jogador: {e}")
        return ""


def buscar_jogos_do_time(nome_time, temporada):
    try:
        with engine.connect() as conn:
            time_row = conn.execute(
                text(
                    "SELECT id, name FROM teams WHERE name ILIKE :t OR nickname ILIKE :t LIMIT 1"
                ),
                {"t": f"%{nome_time}%"},
            ).fetchone()
        if not time_row:
            logger.warning(f"Time nao encontrado: {nome_time}")
            return ""
        with engine.connect() as conn:
            jogos = conn.execute(
                text(
                    "SELECT g.id, g.date_start, g.home_team_id, g.away_team_id, ht.name AS home_name, at.name AS away_name FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE g.season = :temp AND g.status_short = 3 AND (g.home_team_id = :tid OR g.away_team_id = :tid) ORDER BY g.date_start DESC LIMIT 15"
                ),
                {"temp": temporada, "tid": time_row.id},
            ).fetchall()
        if not jogos:
            return ""
        logger.warning(
            f"buscar_jogos_do_time: {time_row.name}, temp={temporada}, {len(jogos)} jogos"
        )
        return _formatar_lista_jogos(time_row.name, str(temporada), jogos, time_row.id)
    except Exception as e:
        logger.error(f"Erro buscar_jogos_do_time: {e}")
        return ""


def buscar_jogos_do_time_por_mes(nome_time, ano, mes):
    try:
        with engine.connect() as conn:
            time_row = conn.execute(
                text(
                    "SELECT id, name FROM teams WHERE name ILIKE :t OR nickname ILIKE :t LIMIT 1"
                ),
                {"t": f"%{nome_time}%"},
            ).fetchone()
        if not time_row:
            logger.warning(f"Time nao encontrado para mes/ano: {nome_time}")
            return ""
        with engine.connect() as conn:
            jogos = conn.execute(
                text(
                    "SELECT g.id, g.date_start, g.home_team_id, g.away_team_id, ht.name AS home_name, at.name AS away_name FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE g.status_short = 3 AND (g.home_team_id = :tid OR g.away_team_id = :tid) AND EXTRACT(YEAR FROM g.date_start) = :ano AND EXTRACT(MONTH FROM g.date_start) = :mes ORDER BY g.date_start ASC LIMIT 20"
                ),
                {"tid": time_row.id, "ano": ano, "mes": mes},
            ).fetchall()
        if not jogos:
            logger.warning(f"Nenhum jogo encontrado: {time_row.name}, {mes}/{ano}")
            return ""
        logger.warning(
            f"buscar_jogos_do_time_por_mes: {time_row.name}, {mes}/{ano}, {len(jogos)} jogos"
        )
        nomes_meses = {
            1: "jan",
            2: "fev",
            3: "mar",
            4: "abr",
            5: "mai",
            6: "jun",
            7: "jul",
            8: "ago",
            9: "set",
            10: "out",
            11: "nov",
            12: "dez",
        }
        label = f"{nomes_meses.get(mes, str(mes))}/{ano}"
        return _formatar_lista_jogos(time_row.name, label, jogos, time_row.id)
    except Exception as e:
        logger.error(f"Erro buscar_jogos_do_time_por_mes: {e}")
        return ""


def _formatar_lista_jogos(nome_time, label_periodo, jogos, team_id):
    if not jogos:
        return ""
    ids_jogos = []
    for jogo in jogos:
        ids_jogos.append(jogo.id)
    mapa_scores = {}
    try:
        with engine.connect() as conn:
            scores = conn.execute(
                text(
                    "SELECT game_id, team_id, points FROM game_team_scores WHERE game_id = ANY(:ids)"
                ),
                {"ids": ids_jogos},
            ).fetchall()
        for s in scores:
            mapa_scores[(s.game_id, s.team_id)] = s.points or 0
    except Exception as e:
        logger.error(f"Erro ao buscar scores em batch: {e}")

    saida = [f"Jogos do {nome_time} em {label_periodo}:"]
    for jogo in jogos:
        if jogo.date_start:
            data = jogo.date_start.strftime("%d/%m/%Y")
        else:
            data = "?"
        eh_casa = jogo.home_team_id == team_id
        if eh_casa:
            local = "Casa"
            adversario = jogo.away_name
            adv_id = jogo.away_team_id
        else:
            local = "Fora"
            adversario = jogo.home_name
            adv_id = jogo.home_team_id
        pts_time = mapa_scores.get((jogo.id, team_id))
        pts_adv = mapa_scores.get((jogo.id, adv_id))
        if pts_time is not None and pts_adv is not None:
            placar = f"{pts_time} x {pts_adv}"
            resultado = "V" if pts_time > pts_adv else "D"
        else:
            placar = "?"
            resultado = "?"
        saida.append(f"  {data} | {local} vs {adversario} | {placar} | {resultado}")
    return "\n".join(saida)


def buscar_temporadas_disponiveis():
    agora = time.time()
    if _cache_temporadas["valor"] and (agora - _cache_temporadas["ts"]) < 3600:
        return _cache_temporadas["valor"]
    try:
        with engine.connect() as conn:
            linhas = conn.execute(
                text("SELECT season FROM seasons ORDER BY season DESC")
            ).fetchall()
        if not linhas:
            return ""
        lista = []
        for l in linhas:  # noqa: E741
            lista.append(str(l.season))
        resultado = "Temporadas no banco: " + ", ".join(lista)
        _cache_temporadas["valor"] = resultado
        _cache_temporadas["ts"] = agora
        return resultado
    except Exception as e:
        logger.error(f"Erro buscar_temporadas_disponiveis: {e}")
        return ""


def buscar_contexto_geral(pergunta):
    pergunta_lower = pergunta.lower()
    partes = []

    temporadas_disponiveis = buscar_temporadas_disponiveis()
    if temporadas_disponiveis:
        partes.append(temporadas_disponiveis)

    mes_mencionado, ano_mencionado = _extrair_mes_ano(pergunta_lower)
    temporadas_mencionadas = _extrair_temporadas(pergunta_lower)
    times_mencionados = _extrair_possiveis_times(pergunta_lower)

    logger.warning(
        f"buscar_contexto_geral: times={times_mencionados}, mes={mes_mencionado}, ano={ano_mencionado}, temporadas={temporadas_mencionadas}"
    )

    for apelido in times_mencionados:
        if mes_mencionado and ano_mencionado:
            jogos = buscar_jogos_do_time_por_mes(
                apelido, ano_mencionado, mes_mencionado
            )
            if jogos:
                partes.append(jogos)
        elif temporadas_mencionadas:
            for temporada in temporadas_mencionadas:
                jogos = buscar_jogos_do_time(apelido, temporada)
                if jogos:
                    partes.append(jogos)
        else:
            jogos = buscar_jogos_do_time(apelido, 2025)
            if jogos:
                partes.append(jogos)

    if not times_mencionados:
        nomes_candidatos = _extrair_possiveis_nomes(pergunta_lower)
        logger.warning(f"buscar_contexto_geral: nomes_candidatos={nomes_candidatos}")

        for nome in nomes_candidatos:
            if temporadas_mencionadas:
                for temporada in temporadas_mencionadas:
                    stats = buscar_stats_jogador_na_temporada(nome, temporada)
                    if stats:
                        partes.append(stats)
            else:
                stats = buscar_stats_recentes_jogador(nome)
                if stats:
                    partes.append(stats)

            info = buscar_jogador_por_nome(nome)
            if info:
                partes.append(info)

    contexto = "\n\n".join(partes)
    logger.warning(f"buscar_contexto_geral: contexto_total={len(contexto)} chars")
    return contexto
