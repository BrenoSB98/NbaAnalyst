import os
from sqlalchemy import create_engine, text

_user = os.getenv("POSTGRES_USER")
_password = os.getenv("POSTGRES_PASSWORD")
_host = os.getenv("POSTGRES_HOST", "postgres")
_port = os.getenv("POSTGRES_PORT", "5432")
_db = os.getenv("POSTGRES_DB")

DATABASE_URL = f"postgresql://{_user}:{_password}@{_host}:{_port}/{_db}"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

_TIMES_CONHECIDOS = [
    "lakers", "celtics", "warriors", "bulls", "heat", "nets", "knicks",
    "bucks", "suns", "clippers", "nuggets", "mavericks", "76ers", "raptors",
    "spurs", "thunder", "jazz", "rockets", "pistons", "hawks", "hornets",
    "pacers", "magic", "wizards", "cavaliers", "timberwolves", "grizzlies",
    "pelicans", "kings", "trail blazers", "blazers",
]

_PALAVRAS_IGNORAR = {
    "jogador", "atleta", "player", "stats", "estatística", "pontos", "assistência", "rebote",
    "temporada", "jogo", "partida", "resultado", "placar", "time", "franquia", "equipe",
    "nba", "qual", "quais", "como", "quando", "onde", "quantos", "quantas", "teve", "fez",
    "média", "total", "melhor", "pior", "mais", "menos",
}

def _extrair_possiveis_times(texto):
    encontrados = []
    for time in _TIMES_CONHECIDOS:
        if time in texto:
            encontrados.append(time)
    return encontrados

def _extrair_possiveis_nomes(texto):
    nomes = []
    for palavra in texto.split():
        palavra_limpa = palavra.strip("?.,!:;").lower()
        if len(palavra_limpa) > 3 and palavra_limpa not in _PALAVRAS_IGNORAR:
            nomes.append(palavra_limpa)
    return nomes

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
                SELECT firstname, lastname, birth_country, nba_start
                FROM players
                WHERE firstname ILIKE :termo OR lastname ILIKE :termo
                LIMIT 10
            """), {"termo": f"%{nome}%"}).fetchall()
        if not linhas:
            return ""
        saida = []
        for l in linhas:
            saida.append(f"- {l.firstname} {l.lastname} | País: {l.birth_country} | Início NBA: {l.nba_start}")
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
                LIMIT 5
            """), {"termo": f"%{nome_jogador}%"}).fetchall()
        if not jogadores:
            return ""
        saida = []
        for jogador in jogadores:
            with engine.connect() as conn:
                stats = conn.execute(text("""
                    SELECT points, assists, tot_reb, steals, blocks
                    FROM player_game_stats
                    WHERE player_id = :pid AND season = :temporada
                """), {"pid": jogador.id, "temporada": temporada}).fetchall()
            if not stats:
                continue
            total_jogos = len(stats)
            media_pontos = round(sum(s.points or 0 for s in stats) / total_jogos, 1)
            media_assistencias = round(sum(s.assists or 0 for s in stats) / total_jogos, 1)
            media_rebotes = round(sum(s.tot_reb or 0 for s in stats) / total_jogos, 1)
            media_roubos = round(sum(s.steals or 0 for s in stats) / total_jogos, 1)
            media_bloqueios = round(sum(s.blocks or 0 for s in stats) / total_jogos, 1)
            bloco = (
                f"Jogador: {jogador.firstname} {jogador.lastname} | Temporada: {temporada}\n"
                f"  Jogos: {total_jogos} | Pontos/jogo: {media_pontos} | Assistências/jogo: {media_assistencias}\n"
                f"  Rebotes/jogo: {media_rebotes} | Roubos/jogo: {media_roubos} | Bloqueios/jogo: {media_bloqueios}"
            )
            saida.append(bloco)
        return "\n\n".join(saida)
    except Exception as e:
        print(f"Erro em buscar_stats_jogador_na_temporada: {e}")
        return ""

def buscar_jogos_do_time(nome_time, temporada):
    try:
        with engine.connect() as conn:
            time = conn.execute(text("""
                SELECT id, name FROM teams WHERE name ILIKE :termo LIMIT 1
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
                  AND (g.home_team_id = :tid OR g.away_team_id = :tid)
                ORDER BY g.date_start
                LIMIT 20
            """), {"temporada": temporada, "tid": time.id}).fetchall()
        if not jogos:
            return ""
        saida = [f"Jogos do time {time.name} na temporada {temporada}:"]
        for jogo in jogos:
            data = jogo.date_start.strftime("%d/%m/%Y") if jogo.date_start else "?"
            eh_casa = jogo.home_team_id == time.id
            local = "Casa" if eh_casa else "Fora"
            adversario = jogo.away_name if eh_casa else jogo.home_name
            adv_id = jogo.away_team_id if eh_casa else jogo.home_team_id
            with engine.connect() as conn:
                score_time = conn.execute(text("""
                    SELECT points, win FROM game_team_scores WHERE game_id = :gid AND team_id = :tid
                """), {"gid": jogo.id, "tid": time.id}).fetchone()
                score_adv = conn.execute(text("""
                    SELECT points FROM game_team_scores WHERE game_id = :gid AND team_id = :tid
                """), {"gid": jogo.id, "tid": adv_id}).fetchone()
            if score_time and score_adv:
                placar = f"{score_time.points} x {score_adv.points}"
                resultado_jogo = "Vitória" if (score_time.win or 0) > 0 else "Derrota"
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
        lista = [str(l.season) for l in linhas]
        return "Temporadas disponíveis: " + ", ".join(lista)
    except Exception as e:
        print(f"Erro em buscar_temporadas_disponiveis: {e}")
        return ""

def buscar_contexto_geral(pergunta):
    pergunta_lower = pergunta.lower()
    partes = []

    temporadas = buscar_temporadas_disponiveis()
    if temporadas:
        partes.append(temporadas)

    if any(p in pergunta_lower for p in ["time", "franquia", "equipe", "times", "franquias"]):
        times = buscar_times()
        if times:
            partes.append("Times NBA disponíveis:\n" + times)

    for temporada in range(2015, 2026):
        if str(temporada) in pergunta_lower:
            if any(p in pergunta_lower for p in ["jogo", "partida", "resultado", "placar"]):
                for nome_time in _extrair_possiveis_times(pergunta_lower):
                    jogos = buscar_jogos_do_time(nome_time, temporada)
                    if jogos:
                        partes.append(jogos)
            if any(p in pergunta_lower for p in ["jogador", "stats", "estatística", "pontos", "assistência", "rebote"]):
                for nome in _extrair_possiveis_nomes(pergunta_lower):
                    stats = buscar_stats_jogador_na_temporada(nome, temporada)
                    if stats:
                        partes.append(stats)

    if any(p in pergunta_lower for p in ["jogador", "atleta", "player"]):
        for nome in _extrair_possiveis_nomes(pergunta_lower):
            jogador = buscar_jogador_por_nome(nome)
            if jogador:
                partes.append("Jogadores encontrados:\n" + jogador)

    if not partes:
        return ""

    return "\n\n".join(partes)