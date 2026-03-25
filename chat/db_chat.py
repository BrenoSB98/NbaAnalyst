import os
from sqlalchemy import create_engine, text

_user = os.getenv("POSTGRES_USER")
_password = os.getenv("POSTGRES_PASSWORD")
_host = os.getenv("POSTGRES_HOST", "postgres")
_port = os.getenv("POSTGRES_PORT", "5432")
_db = os.getenv("POSTGRES_DB")

DATABASE_URL = f"postgresql://{_user}:{_password}@{_host}:{_port}/{_db}"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

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
    "76ers": "Philadelphia 76ers",
    "sixers": "Philadelphia 76ers",
    "raptors": "Toronto Raptors",
    "spurs": "San Antonio Spurs",
    "thunder": "Oklahoma City Thunder",
    "jazz": "Utah Jazz",
    "rockets": "Houston Rockets",
    "pistons": "Detroit Pistons",
    "hawks": "Atlanta Hawks",
    "hornets": "Charlotte Hornets",
    "pacers": "Indiana Pacers",
    "magic": "Orlando Magic",
    "wizards": "Washington Wizards",
    "cavaliers": "Cleveland Cavaliers",
    "cavs": "Cleveland Cavaliers",
    "timberwolves": "Minnesota Timberwolves",
    "wolves": "Minnesota Timberwolves",
    "grizzlies": "Memphis Grizzlies",
    "pelicans": "New Orleans Pelicans",
    "kings": "Sacramento Kings",
    "trail blazers": "Portland Trail Blazers",
    "blazers": "Portland Trail Blazers",
}

_PALAVRAS_IGNORAR = {
    "jogador", "atleta", "player", "stats", "estatistica", "pontos", "assistencia", "rebote",
    "temporada", "jogo", "partida", "resultado", "placar", "time", "franquia", "equipe",
    "nba", "qual", "quais", "como", "quando", "onde", "quantos", "quantas", "teve", "fez",
    "media", "total", "melhor", "pior", "mais", "menos", "voce", "para", "qual", "esse",
    "esta", "esse", "isso", "pelo", "pela", "numa", "numa", "com", "sem", "por",
}

def _extrair_possiveis_times(texto):
    encontrados = []
    for apelido in _APELIDOS_TIMES:
        if apelido in texto:
            encontrados.append(apelido)
    return encontrados

def _extrair_possiveis_nomes(texto):
    nomes = []
    for palavra in texto.split():
        palavra_limpa = palavra.strip("?.,!:;()\"'").lower()
        if len(palavra_limpa) > 3 and palavra_limpa not in _PALAVRAS_IGNORAR:
            nomes.append(palavra_limpa)
    return nomes

def _extrair_temporadas(texto):
    temporadas = []
    for ano in range(2010, 2027):
        if str(ano) in texto:
            temporadas.append(ano)
    return temporadas

def buscar_times():
    try:
        with engine.connect() as conn:
            linhas = conn.execute(text("""
                SELECT name, nickname, city, code
                FROM teams
                WHERE nba_franchise = true
                ORDER BY name
            """)).fetchall()
        if not linhas:
            return ""
        saida = []
        for l in linhas:
            saida.append(f"- {l.name} ({l.nickname}) | Cidade: {l.city} | Código: {l.code}")
        return "\n".join(saida)
    except Exception as e:
        print(f"Erro em buscar_times: {e}")
        return ""

def buscar_jogador_por_nome(nome):
    try:
        with engine.connect() as conn:
            linhas = conn.execute(text("""
                SELECT firstname, lastname, birth_country, nba_start, height, weight
                FROM players
                WHERE firstname ILIKE :termo OR lastname ILIKE :termo
                LIMIT 5
            """), {"termo": f"%{nome}%"}).fetchall()
        if not linhas:
            return ""
        saida = []
        for l in linhas:
            saida.append(f"- {l.firstname} {l.lastname} | País: {l.birth_country} | Início NBA: {l.nba_start} | Altura: {l.height} | Peso: {l.weight}")
        return "\n".join(saida)
    except Exception as e:
        print(f"Erro em buscar_jogador_por_nome: {e}")
        return ""

def buscar_stats_jogador_na_temporada(nome_jogador, temporada):
    try:
        with engine.connect() as conn:
            jogadores = conn.execute(text("""
                SELECT id, firstname, lastname
                FROM players
                WHERE firstname ILIKE :termo OR lastname ILIKE :termo
                LIMIT 3
            """), {"termo": f"%{nome_jogador}%"}).fetchall()
        if not jogadores:
            return ""
        saida = []
        for jogador in jogadores:
            with engine.connect() as conn:
                stats = conn.execute(text("""
                    SELECT points, assists, tot_reb, steals, blocks, turnovers, minutes
                    FROM player_game_stats
                    WHERE player_id = :pid AND season = :temporada
                """), {"pid": jogador.id, "temporada": temporada}).fetchall()
            if not stats:
                continue
            total_jogos = len(stats)

            soma_pontos = 0
            soma_assistencias = 0
            soma_rebotes = 0
            soma_roubos = 0
            soma_bloqueios = 0
            soma_turnovers = 0

            for s in stats:
                soma_pontos = soma_pontos + (s.points or 0)
                soma_assistencias = soma_assistencias + (s.assists or 0)
                soma_rebotes = soma_rebotes + (s.tot_reb or 0)
                soma_roubos = soma_roubos + (s.steals or 0)
                soma_bloqueios = soma_bloqueios + (s.blocks or 0)
                soma_turnovers = soma_turnovers + (s.turnovers or 0)

            media_pts = round(soma_pontos / total_jogos, 1)
            media_ast = round(soma_assistencias / total_jogos, 1)
            media_reb = round(soma_rebotes / total_jogos, 1)
            media_stl = round(soma_roubos / total_jogos, 1)
            media_blk = round(soma_bloqueios / total_jogos, 1)
            media_tov = round(soma_turnovers / total_jogos, 1)

            bloco = (
                f"Jogador: {jogador.firstname} {jogador.lastname} | Temporada: {temporada} | Jogos: {total_jogos}\n"
                f"  Pontos/jogo: {media_pts} | Assistências/jogo: {media_ast} | Rebotes/jogo: {media_reb}\n"
                f"  Roubos/jogo: {media_stl} | Bloqueios/jogo: {media_blk} | Turnovers/jogo: {media_tov}"
            )
            saida.append(bloco)
        return "\n\n".join(saida)
    except Exception as e:
        print(f"Erro em buscar_stats_jogador_na_temporada: {e}")
        return ""

def buscar_stats_recentes_jogador(nome_jogador):
    try:
        with engine.connect() as conn:
            jogadores = conn.execute(text("""
                SELECT id, firstname, lastname
                FROM players
                WHERE firstname ILIKE :termo OR lastname ILIKE :termo
                LIMIT 3
            """), {"termo": f"%{nome_jogador}%"}).fetchall()
        if not jogadores:
            return ""
        saida = []
        for jogador in jogadores:
            with engine.connect() as conn:
                stats = conn.execute(text("""
                    SELECT pgs.points, pgs.assists, pgs.tot_reb, pgs.steals, pgs.blocks, pgs.turnovers, g.season
                    FROM player_game_stats pgs
                    JOIN games g ON g.id = pgs.game_id
                    WHERE pgs.player_id = :pid AND g.status_short = 3
                    ORDER BY g.date_start DESC
                    LIMIT 10
                """), {"pid": jogador.id}).fetchall()
            if not stats:
                continue
            total = len(stats)

            soma_pts = 0
            soma_ast = 0
            soma_reb = 0

            for s in stats:
                soma_pts = soma_pts + (s.points or 0)
                soma_ast = soma_ast + (s.assists or 0)
                soma_reb = soma_reb + (s.tot_reb or 0)

            if stats:
                temporada_ref = stats[0].season 
            else:
                temporada_ref = "?"
            bloco = (
                f"Jogador: {jogador.firstname} {jogador.lastname} | Últimos {total} jogos (temporada {temporada_ref})\n"
                f"  Média: {round(soma_pts/total,1)} pts | {round(soma_ast/total,1)} ast | {round(soma_reb/total,1)} reb"
            )
            saida.append(bloco)
        return "\n\n".join(saida)
    except Exception as e:
        print(f"Erro em buscar_stats_recentes_jogador: {e}")
        return ""

def buscar_jogos_do_time(nome_time, temporada):
    try:
        with engine.connect() as conn:
            time = conn.execute(text("""
                SELECT id, name FROM teams
                WHERE name ILIKE :termo OR nickname ILIKE :termo
                LIMIT 1
            """), {"termo": f"%{nome_time}%"}).fetchone()
        if not time:
            return ""
        with engine.connect() as conn:
            jogos = conn.execute(text("""
                SELECT g.id, g.date_start, g.home_team_id, g.away_team_id,
                    ht.name AS home_name, at.name AS away_name
                FROM games g
                JOIN teams ht ON ht.id = g.home_team_id
                JOIN teams at ON at.id = g.away_team_id
                WHERE g.season = :temporada
                  AND g.status_short = 3
                  AND (g.home_team_id = :tid OR g.away_team_id = :tid)
                ORDER BY g.date_start DESC
                LIMIT 15
            """), {"temporada": temporada, "tid": time.id}).fetchall()
        if not jogos:
            return ""
        saida = [f"Jogos recentes do {time.name} na temporada {temporada}:"]
        for jogo in jogos:
            if jogo.date_start:
                data = jogo.date_start.strftime("%d/%m/%Y")     
            else:
                data = "?"
                
            eh_casa = jogo.home_team_id == time.id
            if eh_casa:
                local = "Casa"     
            else:
                local = "Fora"
            if eh_casa:
                adversario = jogo.away_name 
            else:
                adversario = jogo.home_name
            if eh_casa:
                adv_id = jogo.away_team_id     
            else:
                adv_id = jogo.home_team_id
                
            with engine.connect() as conn:
                score_time = conn.execute(text("SELECT points FROM game_team_scores WHERE game_id = :gid AND team_id = :tid"), {"gid": jogo.id, "tid": time.id}).fetchone()
                score_adv = conn.execute(text("SELECT points FROM game_team_scores WHERE game_id = :gid AND team_id = :tid"), {"gid": jogo.id, "tid": adv_id}).fetchone()
            if score_time and score_adv:
                pts_time = score_time.points or 0
                pts_adv = score_adv.points or 0
                placar = f"{pts_time} x {pts_adv}"
                if pts_time > pts_adv:
                    resultado_jogo = "Vitória"
                else:
                    resultado_jogo = "Derrota"
            else:
                placar = "Sem placar"
                resultado_jogo = "?"
            saida.append(f"  {data} | {local} vs {adversario} | {placar} | {resultado_jogo}")
        return "\n".join(saida)
    except Exception as e:
        print(f"Erro em buscar_jogos_do_time: {e}")
        return ""

def buscar_temporadas_disponiveis():
    try:
        with engine.connect() as conn:
            linhas = conn.execute(text("SELECT season FROM seasons ORDER BY season DESC")).fetchall()
        if not linhas:
            return ""
        lista = []
        for l in linhas:
            lista.append(str(l.season))
        return "Temporadas disponíveis no banco: " + ", ".join(lista)
    except Exception as e:
        print(f"Erro em buscar_temporadas_disponiveis: {e}")
        return ""

def buscar_contexto_geral(pergunta):
    pergunta_lower = pergunta.lower()
    partes = []

    temporadas_disponiveis = buscar_temporadas_disponiveis()
    if temporadas_disponiveis:
        partes.append(temporadas_disponiveis)
        
    if any(p in pergunta_lower for p in ["time", "franquia", "equipe", "times", "franquias", "clube"]):
        times = buscar_times()
        if times:
            partes.append("Times NBA no banco:\n" + times)

    temporadas_mencionadas = _extrair_temporadas(pergunta_lower)
    times_mencionados = _extrair_possiveis_times(pergunta_lower)

    for apelido in times_mencionados:
        if temporadas_mencionadas:
            for temporada in temporadas_mencionadas:
                jogos = buscar_jogos_do_time(apelido, temporada)
                if jogos:
                    partes.append(jogos)
        else:
            jogos = buscar_jogos_do_time(apelido, 2025)
            if jogos:
                partes.append(jogos)

    nomes_candidatos = _extrair_possiveis_nomes(pergunta_lower)

    for nome in nomes_candidatos:
        if temporadas_mencionadas:
            for temporada in temporadas_mencionadas:
                stats = buscar_stats_jogador_na_temporada(nome, temporada)
                if stats:
                    partes.append(stats)
        else:
            stats_recentes = buscar_stats_recentes_jogador(nome)
            if stats_recentes:
                partes.append(stats_recentes)

        info = buscar_jogador_por_nome(nome)
        if info:
            partes.append("Jogadores encontrados:\n" + info)

    if not partes:
        return ""

    return "\n\n".join(partes)