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
    "los angeles lakers": "Los Angeles Lakers",
    "celtics": "Boston Celtics",
    "boston": "Boston Celtics",
    "warriors": "Golden State Warriors",
    "golden state": "Golden State Warriors",
    "bulls": "Chicago Bulls",
    "chicago": "Chicago Bulls",
    "heat": "Miami Heat",
    "miami": "Miami Heat",
    "nets": "Brooklyn Nets",
    "brooklyn": "Brooklyn Nets",
    "knicks": "New York Knicks",
    "new york": "New York Knicks",
    "bucks": "Milwaukee Bucks",
    "milwaukee": "Milwaukee Bucks",
    "suns": "Phoenix Suns",
    "phoenix": "Phoenix Suns",
    "clippers": "LA Clippers",
    "la clippers": "LA Clippers",
    "los angeles clippers": "LA Clippers",
    "nuggets": "Denver Nuggets",
    "denver": "Denver Nuggets",
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

_NOMES_MESES = {
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

_MAPA_STATS = {
    "pontos": "points",
    "ponto": "points",
    "pts": "points",
    "scoring": "points",
    "assistencias": "assists",
    "assistências": "assists",
    "ast": "assists",
    "assistência": "assists",
    "rebotes": "tot_reb",
    "rebote": "tot_reb",
    "reb": "tot_reb",
    "roubos": "steals",
    "roubo": "steals",
    "stl": "steals",
    "tocos": "blocks",
    "toco": "blocks",
    "blk": "blocks",
    "bloqueios": "blocks",
    "bloqueio": "blocks",
    "turnovers": "turnovers",
    "tov": "turnovers",
}

_cache_temporadas = {"valor": None, "ts": 0}
_cache_cobertura = {"valor": None, "ts": 0}


def normalizar_nome_time(texto):
    texto_lower = texto.lower().strip()
    for apelido in _APELIDOS_TIMES:
        if apelido in texto_lower:
            return _APELIDOS_TIMES[apelido]
    return None


def cobertura_banco():
    agora = time.time()
    if _cache_cobertura["valor"] and (agora - _cache_cobertura["ts"]) < 3600:
        return _cache_cobertura["valor"]
    try:
        with engine.connect() as conn:
            linhas = conn.execute(
                text(
                    "SELECT MIN(season) AS min_s, MAX(season) AS max_s FROM games WHERE status_short = 3"
                )
            ).fetchone()
            ultimo = conn.execute(
                text(
                    "SELECT MAX(date_start) AS max_data FROM games WHERE status_short = 3"
                )
            ).fetchone()
        if not linhas or linhas.min_s is None:
            resultado = "Cobertura do banco: indisponível"
        else:
            data_ultima = (
                ultimo.max_data.strftime("%d/%m/%Y")
                if ultimo and ultimo.max_data
                else "?"
            )
            resultado = f"Cobertura do banco: temporadas {linhas.min_s} a {linhas.max_s}, último jogo registrado em {data_ultima}"
        _cache_cobertura["valor"] = resultado
        _cache_cobertura["ts"] = agora
        return resultado
    except Exception as e:
        logger.error(f"Erro cobertura_banco: {e}")
        return "Cobertura do banco: indisponível"


def _buscar_jogador_id(nome):
    partes = nome.strip().split()
    try:
        with engine.connect() as conn:
            if len(partes) >= 2:
                linha = conn.execute(
                    text(
                        "SELECT id, firstname, lastname FROM players WHERE (firstname ILIKE :p AND lastname ILIKE :u) OR (firstname ILIKE :u AND lastname ILIKE :p) LIMIT 1"
                    ),
                    {"p": f"%{partes[0]}%", "u": f"%{partes[-1]}%"},
                ).fetchone()
            else:
                linha = conn.execute(
                    text(
                        "SELECT id, firstname, lastname FROM players WHERE lastname ILIKE :t OR firstname ILIKE :t LIMIT 1"
                    ),
                    {"t": f"%{nome}%"},
                ).fetchone()
        return linha
    except Exception as e:
        logger.error(f"Erro _buscar_jogador_id: {e}")
        return None


def stats_jogador_temporada(nome_jogador, temporada):
    logger.warning(
        f"stats_jogador_temporada: nome={nome_jogador!r}, temporada={temporada}"
    )
    jogador = _buscar_jogador_id(nome_jogador)
    if not jogador:
        return (
            f"Jogador '{nome_jogador}' não encontrado no banco.\n" + cobertura_banco()
        )
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text(
                    "SELECT COUNT(*) AS jogos, ROUND(AVG(points)::numeric, 1) AS pts, ROUND(AVG(assists)::numeric, 1) AS ast, ROUND(AVG(tot_reb)::numeric, 1) AS reb, ROUND(AVG(steals)::numeric, 1) AS stl, ROUND(AVG(blocks)::numeric, 1) AS blk, ROUND(AVG(turnovers)::numeric, 1) AS tov, ROUND(AVG(fgp)::numeric, 1) AS fgp, ROUND(AVG(tpp)::numeric, 1) AS tpp FROM player_game_stats WHERE player_id = :pid AND season = :t"
                ),
                {"pid": jogador.id, "t": temporada},
            ).fetchone()
        if not row or row.jogos == 0:
            return (
                f"Sem dados de {jogador.firstname} {jogador.lastname} na temporada {temporada}.\n"
                + cobertura_banco()
            )
        saida = []
        saida.append(
            f"Stats de {jogador.firstname} {jogador.lastname} na temporada {temporada}:"
        )
        saida.append(f"  Jogos: {row.jogos}")
        saida.append(
            f"  Pontos: {row.pts} | Assistências: {row.ast} | Rebotes: {row.reb}"
        )
        saida.append(f"  Roubos: {row.stl} | Tocos: {row.blk} | Turnovers: {row.tov}")
        saida.append(f"  FG%: {row.fgp} | 3P%: {row.tpp}")
        saida.append(cobertura_banco())
        return "\n".join(saida)
    except Exception as e:
        logger.error(f"Erro stats_jogador_temporada: {e}")
        return "Erro ao consultar estatísticas do jogador."


def jogos_time(nome_time, ano, mes=None):
    logger.warning(f"jogos_time: time={nome_time!r}, ano={ano}, mes={mes}")
    nome_oficial = normalizar_nome_time(nome_time)
    if not nome_oficial:
        return f"Time '{nome_time}' não reconhecido."
    try:
        with engine.connect() as conn:
            time_row = conn.execute(
                text(
                    "SELECT id, name FROM teams WHERE name ILIKE :t OR nickname ILIKE :t LIMIT 1"
                ),
                {"t": f"%{nome_oficial}%"},
            ).fetchone()
        if not time_row:
            return (
                f"Time '{nome_oficial}' não encontrado no banco.\n" + cobertura_banco()
            )
        with engine.connect() as conn:
            if mes is not None:
                jogos = conn.execute(
                    text(
                        "SELECT g.id, g.date_start, g.home_team_id, g.away_team_id, ht.name AS home_name, at.name AS away_name FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE g.status_short = 3 AND (g.home_team_id = :tid OR g.away_team_id = :tid) AND EXTRACT(YEAR FROM g.date_start) = :ano AND EXTRACT(MONTH FROM g.date_start) = :mes ORDER BY g.date_start ASC LIMIT 20"
                    ),
                    {"tid": time_row.id, "ano": ano, "mes": mes},
                ).fetchall()
                label = f"{_NOMES_MESES.get(mes, str(mes))}/{ano}"
            else:
                jogos = conn.execute(
                    text(
                        "SELECT g.id, g.date_start, g.home_team_id, g.away_team_id, ht.name AS home_name, at.name AS away_name FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE g.season = :temp AND g.status_short = 3 AND (g.home_team_id = :tid OR g.away_team_id = :tid) ORDER BY g.date_start DESC LIMIT 15"
                    ),
                    {"temp": ano, "tid": time_row.id},
                ).fetchall()
                label = f"temporada {ano}"
        MIN_JOGOS_RETORNO = 3
        if not jogos:
            return (
                f"Nenhum jogo do {time_row.name} encontrado em {label} no banco. Para resultados recentes ou em curso, use buscar_web.\n"
                + cobertura_banco()
            )
        if len(jogos) < MIN_JOGOS_RETORNO:
            return (
                f"Apenas {len(jogos)} jogo(s) do {time_row.name} encontrado(s) em {label} no banco — dados incompletos. Para resultados recentes ou em curso, use buscar_web em vez do banco.\n"
                + cobertura_banco()
            )
        return _formatar_lista_jogos(time_row.name, label, jogos, time_row.id)
    except Exception as e:
        logger.error(f"Erro jogos_time: {e}")
        return "Erro ao consultar jogos do time."


def lideres_liga(estatistica, temporada, top_n=10):
    logger.warning(
        f"lideres_liga: stat={estatistica!r}, temporada={temporada}, top_n={top_n}"
    )
    coluna = _MAPA_STATS.get(estatistica.lower())
    if not coluna:
        opcoes = ", ".join(sorted(set(_MAPA_STATS.values())))
        return f"Estatística '{estatistica}' não reconhecida. Disponíveis: {opcoes}."
    if top_n < 1 or top_n > 30:
        top_n = 10
    try:
        consulta = f"SELECT p.firstname, p.lastname, COUNT(*) AS jogos, ROUND(AVG(pgs.{coluna})::numeric, 1) AS media FROM player_game_stats pgs JOIN players p ON p.id = pgs.player_id WHERE pgs.season = :t GROUP BY p.id, p.firstname, p.lastname HAVING COUNT(*) >= 10 ORDER BY media DESC LIMIT :n"
        with engine.connect() as conn:
            linhas = conn.execute(
                text(consulta), {"t": temporada, "n": top_n}
            ).fetchall()
        if not linhas:
            return (
                f"Sem dados de líderes em {estatistica} para a temporada {temporada} no banco. Para dados de temporada em curso, use buscar_web.\n"
                + cobertura_banco()
            )
        if len(linhas) < 3:
            return (
                f"Apenas {len(linhas)} jogador(es) com dados suficientes em {estatistica} na temporada {temporada} no banco — dados incompletos. Para resultados de temporada em curso, use buscar_web.\n"
                + cobertura_banco()
            )
        saida = []
        saida.append(f"Top {len(linhas)} em {estatistica} na temporada {temporada}:")
        for i, l in enumerate(linhas, start=1):  # noqa: E741
            saida.append(
                f"  {i}. {l.firstname} {l.lastname} — {l.media} ({l.jogos} jogos)"
            )
        saida.append(cobertura_banco())
        return "\n".join(saida)
    except Exception as e:
        logger.error(f"Erro lideres_liga: {e}")
        return "Erro ao consultar líderes da liga."


def comparar_jogadores(nomes, temporada):
    logger.warning(f"comparar_jogadores: nomes={nomes}, temporada={temporada}")
    if not nomes or len(nomes) < 2:
        return "Para comparar é preciso informar pelo menos 2 jogadores."
    if len(nomes) > 5:
        nomes = nomes[:5]
    saida = []
    saida.append(f"Comparativo na temporada {temporada}:")
    encontrados = 0
    for nome in nomes:
        jogador = _buscar_jogador_id(nome)
        if not jogador:
            saida.append(f"  {nome}: não encontrado no banco")
            continue
        try:
            with engine.connect() as conn:
                row = conn.execute(
                    text(
                        "SELECT COUNT(*) AS jogos, ROUND(AVG(points)::numeric, 1) AS pts, ROUND(AVG(assists)::numeric, 1) AS ast, ROUND(AVG(tot_reb)::numeric, 1) AS reb, ROUND(AVG(fgp)::numeric, 1) AS fgp FROM player_game_stats WHERE player_id = :pid AND season = :t"
                    ),
                    {"pid": jogador.id, "t": temporada},
                ).fetchone()
            if not row or row.jogos == 0:
                saida.append(
                    f"  {jogador.firstname} {jogador.lastname}: sem dados em {temporada}"
                )
                continue
            saida.append(
                f"  {jogador.firstname} {jogador.lastname} ({row.jogos}j): Pts {row.pts} | Ast {row.ast} | Reb {row.reb} | FG% {row.fgp}"
            )
            encontrados = encontrados + 1
        except Exception as e:
            logger.error(f"Erro comparar_jogadores ({nome}): {e}")
            saida.append(f"  {nome}: erro na consulta")
    saida.append(cobertura_banco())
    if encontrados == 0:
        return (
            "Nenhum dos jogadores tem dados na temporada solicitada.\n"
            + cobertura_banco()
        )
    return "\n".join(saida)


def classificacao_temporada(conferencia, temporada):
    logger.warning(
        f"classificacao_temporada: conf={conferencia!r}, temporada={temporada}"
    )
    conf_lower = (conferencia or "").lower().strip()
    try:
        consulta = """
            SELECT t.name, t.code,
                   SUM(CASE WHEN gts.team_id = t.id AND gts.points > opp.points THEN 1 ELSE 0 END) AS vitorias,
                   SUM(CASE WHEN gts.team_id = t.id AND gts.points < opp.points THEN 1 ELSE 0 END) AS derrotas
            FROM teams t
            JOIN game_team_scores gts ON gts.team_id = t.id
            JOIN games g ON g.id = gts.game_id
            JOIN game_team_scores opp ON opp.game_id = g.id AND opp.team_id <> t.id
            WHERE g.season = :t AND g.status_short = 3 AND t.nba_franchise = TRUE
            GROUP BY t.id, t.name, t.code
            ORDER BY vitorias DESC
        """
        with engine.connect() as conn:
            linhas = conn.execute(text(consulta), {"t": temporada}).fetchall()
        if not linhas:
            return (
                f"Sem dados de classificação para a temporada {temporada} no banco. Para classificação de temporada em curso, use buscar_web.\n"
                + cobertura_banco()
            )
        if len(linhas) < 20:
            return (
                f"Apenas {len(linhas)} time(s) com dados na temporada {temporada} no banco — dados incompletos. Para classificação de temporada em curso, use buscar_web.\n"
                + cobertura_banco()
            )
        saida = []
        saida.append(f"Classificação da temporada {temporada}:")
        for i, l in enumerate(linhas[:15], start=1):  # noqa: E741
            total = (l.vitorias or 0) + (l.derrotas or 0)
            saida.append(
                f"  {i}. {l.name} — {l.vitorias}V-{l.derrotas}D ({total} jogos)"
            )
        if conf_lower in ("leste", "east", "eastern"):
            saida.append(
                "(Filtro por conferência não disponível no banco — listagem geral por vitórias)"
            )
        elif conf_lower in ("oeste", "west", "western"):
            saida.append(
                "(Filtro por conferência não disponível no banco — listagem geral por vitórias)"
            )
        saida.append(cobertura_banco())
        return "\n".join(saida)
    except Exception as e:
        logger.error(f"Erro classificacao_temporada: {e}")
        return "Erro ao consultar classificação."


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
    saida.append(cobertura_banco())
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
