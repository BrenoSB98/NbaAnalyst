from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, or_, and_
from sqlalchemy.orm import Session

from app.db.db_utils import get_db
from app.db.models import Game, GameTeamScore, GameTeamStats, League, Player, PlayerGameStats, PlayerTeamSeason, Season, Team, TeamLeagueInfo
from app.core.logging_config import configurar_logger
from app.routers.auth import obter_usuario_atual
from app.routers import analytics, predictions, bet, onerb, auth, backtest

logger = configurar_logger(__name__)

router = APIRouter()
router.include_router(analytics.router, prefix="/analiticos", tags=["Analíticos"])
router.include_router(predictions.router, prefix="/predicoes", tags=["Predições"])
router.include_router(bet.router, prefix="/apostas", tags=["Apostas"])
router.include_router(onerb.router, prefix="/onerb", tags=["OneRB"])
router.include_router(auth.router, prefix="/autenticacao", tags=["Autenticação"])
router.include_router(backtest.router, prefix="/backtest", tags=["Backtest"])

@router.get("/temporadas")
def listar_temporadas(db: Session = Depends(get_db)):
    temporadas = db.query(Season).order_by(Season.season.desc()).all()
    logger.info("Listando temporadas.")

    lista_temporadas = []
    for temporada in temporadas:
        lista_temporadas.append({"season": temporada.season})
    return {"total": len(lista_temporadas), "temporadas": lista_temporadas}

@router.get("/ligas")
def listar_ligas(db: Session = Depends(get_db)):
    ligas = db.query(League).all()

    lista_ligas = []
    for liga in ligas:
        lista_ligas.append({"id": liga.id, "code": liga.code, "descricao": liga.description})
    return {"total": len(lista_ligas), "ligas": lista_ligas}

@router.get("/times")
def listar_times(page: int = Query(1, ge=1), page_size: int = Query(30, ge=1, le=100), nba_franchise: bool = Query(None), cidade: str = Query(None), nome: str = Query(None), db: Session = Depends(get_db)):
    logger.info(f"Listando times — filtros: nba_franchise={nba_franchise}, cidade={cidade}, nome={nome}")

    query = db.query(Team)

    if nba_franchise is not None:
        query = query.filter(Team.nba_franchise == nba_franchise)
    if cidade:
        query = query.filter(Team.city.ilike(f"%{cidade}%"))
    if nome:
        query = query.filter(Team.name.ilike(f"%{nome}%"))

    total = query.count()
    offset = (page - 1) * page_size
    times = query.order_by(Team.name.asc()).offset(offset).limit(page_size).all()

    lista_times = []
    for time in times:
        lista_times.append({
            "id": time.id,
            "nome": time.name,
            "apelido": time.nickname,
            "codigo": time.code,
            "cidade": time.city,
            "logo": time.logo,
            "nba_franchise": time.nba_franchise,
            "all_star": time.all_star,
        })
    return {"total": total, "pagina": page, "tamanho_pagina": page_size, "times": lista_times}

@router.get("/times/comparar")
def comparar_times(time1_id: int = Query(...), time2_id: int = Query(...), temporada: int = Query(2023), db: Session = Depends(get_db), usuario_atual: dict = Depends(obter_usuario_atual)):
    time1 = db.query(Team).filter(Team.id == time1_id).first()
    time2 = db.query(Team).filter(Team.id == time2_id).first()

    if not time1 or not time2:
        logger.warning(f"Comparação de times falhou — time1_id={time1_id}, time2_id={time2_id} não encontrados.")
        raise HTTPException(status_code=404, detail="Um ou ambos os times não foram encontrados.")

    jogos_time1 = (db.query(Game, GameTeamScore).join(GameTeamScore, GameTeamScore.game_id == Game.id)
                   .filter(Game.season == temporada, GameTeamScore.team_id == time1_id, Game.status_short == 3).all())

    vitorias_time1 = 0
    derrotas_time1 = 0

    for jogo_data in jogos_time1:
        jogo = jogo_data[0]
        score = jogo_data[1]
        adversario = db.query(GameTeamScore).filter(GameTeamScore.game_id == jogo.id, GameTeamScore.team_id != time1_id).first()
        if adversario:
            if score.points > adversario.points:
                vitorias_time1 = vitorias_time1 + 1
            else:
                derrotas_time1 = derrotas_time1 + 1

    jogos_time2 = (db.query(Game, GameTeamScore).join(GameTeamScore, GameTeamScore.game_id == Game.id)
                   .filter(Game.season == temporada, GameTeamScore.team_id == time2_id, Game.status_short == 3).all())

    vitorias_time2 = 0
    derrotas_time2 = 0

    for jogo_data in jogos_time2:
        jogo = jogo_data[0]
        score = jogo_data[1]
        adversario = db.query(GameTeamScore).filter(GameTeamScore.game_id == jogo.id, GameTeamScore.team_id != time2_id).first()
        if adversario:
            if score.points > adversario.points:
                vitorias_time2 = vitorias_time2 + 1
            else:
                derrotas_time2 = derrotas_time2 + 1

    total_time1 = vitorias_time1 + derrotas_time1
    win_rate_time1 = 0
    if total_time1 > 0:
        win_rate_time1 = round(vitorias_time1 / total_time1 * 100, 2)

    total_time2 = vitorias_time2 + derrotas_time2
    win_rate_time2 = 0
    if total_time2 > 0:
        win_rate_time2 = round(vitorias_time2 / total_time2 * 100, 2)

    confrontos = (db.query(Game).filter(Game.season == temporada,or_(and_(Game.home_team_id == time1_id, Game.away_team_id == time2_id),
                                                                     and_(Game.home_team_id == time2_id, Game.away_team_id == time1_id)),
                                        Game.status_short == 3).all())

    vitorias_h2h_time1 = 0
    vitorias_h2h_time2 = 0

    for jogo in confrontos:
        scores = db.query(GameTeamScore).filter(GameTeamScore.game_id == jogo.id).all()
        home_points = None
        away_points = None

        for score in scores:
            if score.is_home:
                home_points = score.points
            else:
                away_points = score.points

        if home_points is not None and away_points is not None:
            if jogo.home_team_id == time1_id:
                if home_points > away_points:
                    vitorias_h2h_time1 = vitorias_h2h_time1 + 1
                else:
                    vitorias_h2h_time2 = vitorias_h2h_time2 + 1
            else:
                if away_points > home_points:
                    vitorias_h2h_time1 = vitorias_h2h_time1 + 1
                else:
                    vitorias_h2h_time2 = vitorias_h2h_time2 + 1
    return {
        "temporada": temporada,
        "time1": {"id": time1.id, "nome": time1.name, "vitorias": vitorias_time1, "derrotas": derrotas_time1, "aproveitamento": win_rate_time1},
        "time2": {"id": time2.id, "nome": time2.name, "vitorias": vitorias_time2, "derrotas": derrotas_time2, "aproveitamento": win_rate_time2},
        "confronto_direto": {"total_jogos": len(confrontos), "vitorias_time1": vitorias_h2h_time1, "vitorias_time2": vitorias_h2h_time2},
    }

@router.get("/times/{time_id}")
def obter_time(time_id: int, db: Session = Depends(get_db)):
    time = db.query(Team).filter(Team.id == time_id).first()
    if not time:
        logger.warning(f"Time não encontrado: id={time_id}")
        raise HTTPException(status_code=404, detail="Time não encontrado.")

    league_info_query = (db.query(TeamLeagueInfo, League).join(League, TeamLeagueInfo.league_id == League.id).filter(TeamLeagueInfo.team_id == time_id).first())

    resultado = {
        "id": time.id,
        "nome": time.name,
        "apelido": time.nickname,
        "codigo": time.code,
        "cidade": time.city,
        "logo": time.logo,
        "all_star": time.all_star,
        "nba_franchise": time.nba_franchise,
        "info_liga": None,
    }

    if league_info_query:
        info = league_info_query[0]
        liga = league_info_query[1]
        resultado["info_liga"] = {"liga": liga.code, "conferencia": info.conference, "divisao": info.division}
    return resultado

@router.get("/times/{time_id}/elenco")
def obter_elenco(time_id: int, temporada: int = Query(2023), db: Session = Depends(get_db)):
    time = db.query(Team).filter(Team.id == time_id).first()
    if not time:
        logger.warning(f"Time não encontrado ao buscar elenco: id={time_id}")
        raise HTTPException(status_code=404, detail="Time não encontrado.")

    jogadores_query = (db.query(Player, PlayerTeamSeason).join(PlayerTeamSeason, PlayerTeamSeason.player_id == Player.id)
                       .filter(PlayerTeamSeason.team_id == time_id, PlayerTeamSeason.season == temporada).all())

    lista_jogadores = []
    for jogador_data in jogadores_query:
        jogador = jogador_data[0]
        pts = jogador_data[1]

        altura_metros = None
        if jogador.height_meters is not None:
            altura_metros = float(jogador.height_meters)

        peso_kg = None
        if jogador.weight_kilograms is not None:
            peso_kg = float(jogador.weight_kilograms)

        lista_jogadores.append({
            "id": jogador.id,
            "nome": f"{jogador.firstname} {jogador.lastname}",
            "camisa": pts.jersey,
            "posicao": pts.pos,
            "ativo": pts.active,
            "altura_metros": altura_metros,
            "peso_kg": peso_kg,
        })
    return {"time_id": time_id, "nome_time": time.name, "temporada": temporada, "total": len(lista_jogadores), "jogadores": lista_jogadores}

@router.get("/times/{time_id}/estatisticas")
def estatisticas_time(time_id: int, temporada: int = Query(2023), db: Session = Depends(get_db), usuario_atual: dict = Depends(obter_usuario_atual)):
    time = db.query(Team).filter(Team.id == time_id).first()
    if not time:
        logger.warning(f"Time não encontrado ao buscar estatísticas: id={time_id}")
        raise HTTPException(status_code=404, detail="Time não encontrado.")

    total_jogos = db.query(Game).filter(or_(Game.home_team_id == time_id, Game.away_team_id == time_id), Game.season == temporada).count()
    jogos_casa = db.query(Game).filter(Game.home_team_id == time_id, Game.season == temporada).count()
    jogos_fora = db.query(Game).filter(Game.away_team_id == time_id, Game.season == temporada).count()
    total_jogadores = db.query(PlayerTeamSeason).filter(PlayerTeamSeason.team_id == time_id, PlayerTeamSeason.season == temporada).count()

    jogos_finalizados = (db.query(Game, GameTeamScore).join(GameTeamScore, GameTeamScore.game_id == Game.id)
                         .filter(Game.season == temporada, GameTeamScore.team_id == time_id, Game.status_short == 3).all())

    vitorias = 0
    derrotas = 0
    for jogo_data in jogos_finalizados:
        jogo = jogo_data[0]
        score = jogo_data[1]
        adversario = db.query(GameTeamScore).filter(GameTeamScore.game_id == jogo.id, GameTeamScore.team_id != time_id).first()
        if adversario:
            if score.points > adversario.points:
                vitorias = vitorias + 1
            else:
                derrotas = derrotas + 1

    total_finalizados = vitorias + derrotas
    aproveitamento = 0
    if total_finalizados > 0:
        aproveitamento = round(vitorias / total_finalizados * 100, 2)
    return {
        "time_id": time_id,
        "nome_time": time.name,
        "temporada": temporada,
        "total_jogos": total_jogos,
        "jogos_casa": jogos_casa,
        "jogos_fora": jogos_fora,
        "total_jogadores": total_jogadores,
        "vitorias": vitorias,
        "derrotas": derrotas,
        "aproveitamento": aproveitamento,
    }

@router.get("/times/{time_id}/performance")
def performance_time(time_id: int, temporada: int = Query(2023), db: Session = Depends(get_db), usuario_atual: dict = Depends(obter_usuario_atual)):
    time = db.query(Team).filter(Team.id == time_id).first()
    if not time:
        logger.warning(f"Time não encontrado ao buscar performance: id={time_id}")
        raise HTTPException(status_code=404, detail="Time não encontrado.")

    jogos = (db.query(Game, GameTeamScore).join(GameTeamScore, GameTeamScore.game_id == Game.id)
             .filter(Game.season == temporada, GameTeamScore.team_id == time_id, Game.status_short == 3)
             .order_by(Game.date_start.desc()).all())

    if len(jogos) == 0:
        return {"time_id": time_id, "nome_time": time.name, "temporada": temporada, "mensagem": "Sem jogos finalizados nesta temporada."}

    total_pontos_feitos = 0
    total_pontos_sofridos = 0
    vitorias_casa = 0
    derrotas_casa = 0
    vitorias_fora = 0
    derrotas_fora = 0
    ultimos_5 = []
    contador = 0

    for jogo_data in jogos:
        jogo = jogo_data[0]
        score = jogo_data[1]

        adversario = db.query(GameTeamScore).filter(GameTeamScore.game_id == jogo.id, GameTeamScore.team_id != time_id).first()
        if not adversario:
            continue

        pontos_feitos = score.points if score.points is not None else 0
        pontos_sofridos = adversario.points if adversario.points is not None else 0

        total_pontos_feitos = total_pontos_feitos + pontos_feitos
        total_pontos_sofridos = total_pontos_sofridos + pontos_sofridos

        vitoria = pontos_feitos > pontos_sofridos
        em_casa = score.is_home

        if em_casa:
            if vitoria:
                vitorias_casa = vitorias_casa + 1
            else:
                derrotas_casa = derrotas_casa + 1
        else:
            if vitoria:
                vitorias_fora = vitorias_fora + 1
            else:
                derrotas_fora = derrotas_fora + 1

        if contador < 5:
            adversario_id = jogo.away_team_id if em_casa else jogo.home_team_id
            resultado = "V" if vitoria else "D"
            ultimos_5.append({
                "jogo_id": jogo.id,
                "data": jogo.date_start,
                "adversario_id": adversario_id,
                "em_casa": em_casa,
                "pontos_feitos": pontos_feitos,
                "pontos_sofridos": pontos_sofridos,
                "resultado": resultado,
            })

        contador = contador + 1

    total_jogos = len(jogos)
    total_vitorias = vitorias_casa + vitorias_fora
    total_derrotas = derrotas_casa + derrotas_fora

    media_pontos_feitos = 0
    media_pontos_sofridos = 0
    diferencial = 0
    aproveitamento = 0

    if total_jogos > 0:
        media_pontos_feitos = round(total_pontos_feitos / total_jogos, 2)
        media_pontos_sofridos = round(total_pontos_sofridos / total_jogos, 2)
        diferencial = round((total_pontos_feitos - total_pontos_sofridos) / total_jogos, 2)
        aproveitamento = round(total_vitorias / total_jogos * 100, 2)
    return {
        "time_id": time_id,
        "nome_time": time.name,
        "temporada": temporada,
        "total_jogos": total_jogos,
        "vitorias": total_vitorias,
        "derrotas": total_derrotas,
        "aproveitamento": aproveitamento,
        "record_casa": f"{vitorias_casa}-{derrotas_casa}",
        "record_fora": f"{vitorias_fora}-{derrotas_fora}",
        "media_pontos_feitos": media_pontos_feitos,
        "media_pontos_sofridos": media_pontos_sofridos,
        "diferencial_pontos": diferencial,
        "ultimos_5_jogos": ultimos_5,
    }

@router.get("/jogos")
def listar_jogos(temporada: int = Query(None), time_id: int = Query(None), data_inicio: str = Query(None), data_fim: str = Query(None),
                 status: int = Query(None), page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    logger.info(f"Listando jogos — temporada={temporada}, time_id={time_id}, status={status}")

    query = db.query(Game)

    if temporada is not None:
        query = query.filter(Game.season == temporada)
    if time_id is not None:
        query = query.filter(or_(Game.home_team_id == time_id, Game.away_team_id == time_id))
    if data_inicio:
        query = query.filter(Game.date_start >= data_inicio)
    if data_fim:
        query = query.filter(Game.date_start <= data_fim)
    if status is not None:
        query = query.filter(Game.status_short == status)

    total = query.count()
    offset = (page - 1) * page_size
    jogos = query.order_by(Game.date_start.desc()).offset(offset).limit(page_size).all()

    lista_jogos = []
    for jogo in jogos:
        scores = db.query(GameTeamScore).filter(GameTeamScore.game_id == jogo.id).all()

        pontos_casa = None
        pontos_fora = None
        for score in scores:
            if score.is_home:
                pontos_casa = score.points
            else:
                pontos_fora = score.points

        lista_jogos.append({
            "id": jogo.id,
            "temporada": jogo.season,
            "liga": jogo.league,
            "data_inicio": jogo.date_start,
            "status_short": jogo.status_short,
            "status_long": jogo.status_long,
            "time_casa_id": jogo.home_team_id,
            "time_fora_id": jogo.away_team_id,
            "pontos_casa": pontos_casa,
            "pontos_fora": pontos_fora,
            "arena": jogo.arena_name,
            "cidade": jogo.arena_city,
        })
    return {"total": total, "pagina": page, "tamanho_pagina": page_size, "jogos": lista_jogos}

@router.get("/jogos/proximos")
def proximos_jogos(dias: int = Query(7, ge=1, le=30), time_id: int = Query(None), db: Session = Depends(get_db)):
    hoje = datetime.now()
    data_limite = hoje + timedelta(days=dias)

    query = db.query(Game).filter(Game.date_start >= hoje, Game.date_start <= data_limite, Game.status_short == 1)

    if time_id:
        query = query.filter(or_(Game.home_team_id == time_id, Game.away_team_id == time_id))

    jogos = query.order_by(Game.date_start.asc()).all()

    lista_jogos = []
    for jogo in jogos:
        time_casa = db.query(Team).filter(Team.id == jogo.home_team_id).first()
        time_fora = db.query(Team).filter(Team.id == jogo.away_team_id).first()

        nome_casa = time_casa.name if time_casa else None
        nome_fora = time_fora.name if time_fora else None

        lista_jogos.append({
            "id": jogo.id,
            "data_inicio": jogo.date_start,
            "time_casa": {"id": jogo.home_team_id, "nome": nome_casa},
            "time_fora": {"id": jogo.away_team_id, "nome": nome_fora},
            "arena": jogo.arena_name,
        })
    return {"total": len(lista_jogos), "dias": dias, "jogos": lista_jogos}

@router.get("/jogos/{jogo_id}")
def obter_jogo(jogo_id: int, db: Session = Depends(get_db)):
    jogo = db.query(Game).filter(Game.id == jogo_id).first()
    if not jogo:
        logger.warning(f"Jogo não encontrado: id={jogo_id}")
        raise HTTPException(status_code=404, detail="Jogo não encontrado.")

    scores = db.query(GameTeamScore).filter(GameTeamScore.game_id == jogo_id).all()

    info_casa = {"id": jogo.home_team_id, "nome": None, "apelido": None, "logo": None, "pontos": None, "parciais": None}
    info_fora = {"id": jogo.away_team_id, "nome": None, "apelido": None, "logo": None, "pontos": None, "parciais": None}

    time_casa = db.query(Team).filter(Team.id == jogo.home_team_id).first()
    time_fora = db.query(Team).filter(Team.id == jogo.away_team_id).first()

    if time_casa:
        info_casa["nome"] = time_casa.name
        info_casa["apelido"] = time_casa.nickname
        info_casa["logo"] = time_casa.logo

    if time_fora:
        info_fora["nome"] = time_fora.name
        info_fora["apelido"] = time_fora.nickname
        info_fora["logo"] = time_fora.logo

    for score in scores:
        parciais = {"q1": score.linescore_q1, "q2": score.linescore_q2, "q3": score.linescore_q3, "q4": score.linescore_q4}
        if score.is_home:
            info_casa["pontos"] = score.points
            info_casa["parciais"] = parciais
        else:
            info_fora["pontos"] = score.points
            info_fora["parciais"] = parciais

    return {
        "id": jogo.id,
        "temporada": jogo.season,
        "liga": jogo.league,
        "data_inicio": jogo.date_start,
        "data_fim": jogo.date_end,
        "duracao": jogo.duration,
        "status_short": jogo.status_short,
        "status_long": jogo.status_long,
        "fase": jogo.stage,
        "periodos_atual": jogo.periods_current,
        "periodos_total": jogo.periods_total,
        "arena": {"nome": jogo.arena_name, "cidade": jogo.arena_city, "estado": jogo.arena_state, "pais": jogo.arena_country},
        "time_casa": info_casa,
        "time_fora": info_fora,
        "empates": jogo.times_tied,
        "mudancas_lideranca": jogo.lead_changes,
        "nugget": jogo.nugget,
    }

@router.get("/jogos/{jogo_id}/estatisticas-times")
def estatisticas_times_jogo(jogo_id: int, db: Session = Depends(get_db)):
    jogo = db.query(Game).filter(Game.id == jogo_id).first()
    if not jogo:
        logger.warning(f"Jogo não encontrado ao buscar estatísticas de times: id={jogo_id}")
        raise HTTPException(status_code=404, detail="Jogo não encontrado.")

    stats = db.query(GameTeamStats).filter(GameTeamStats.game_id == jogo_id).all()

    lista_stats = []
    for stat in stats:
        time = db.query(Team).filter(Team.id == stat.team_id).first()
        nome_time = time.name if time else None

        lista_stats.append({
            "time_id": stat.team_id,
            "nome_time": nome_time,
            "pontos": stat.points,
            "fgm": stat.fgm, "fga": stat.fga, "fgp": float(stat.fgp) if stat.fgp is not None else None,
            "ftm": stat.ftm, "fta": stat.fta, "ftp": float(stat.ftp) if stat.ftp is not None else None,
            "tpm": stat.tpm, "tpa": stat.tpa, "tpp": float(stat.tpp) if stat.tpp is not None else None,
            "rebotes_ofensivos": stat.off_reb,
            "rebotes_defensivos": stat.def_reb,
            "rebotes_totais": stat.tot_reb,
            "assistencias": stat.assists,
            "roubos": stat.steals,
            "bloqueios": stat.blocks,
            "turnovers": stat.turnovers,
            "faltas": stat.p_fouls,
            "plus_minus": stat.plus_minus,
            "fast_break_points": stat.fast_break_points,
            "pontos_no_garrafao": stat.points_in_paint,
            "segundas_chances": stat.second_chance_points,
            "pontos_apos_turnover": stat.points_off_turnovers,
            "maior_vantagem": stat.biggest_lead,
            "maior_sequencia": stat.longest_run,
        })
    return {"jogo_id": jogo_id, "estatisticas_times": lista_stats}

@router.get("/jogos/{jogo_id}/estatisticas-jogadores")
def estatisticas_jogadores_jogo(jogo_id: int, db: Session = Depends(get_db)):
    jogo = db.query(Game).filter(Game.id == jogo_id).first()
    if not jogo:
        logger.warning(f"Jogo não encontrado ao buscar estatísticas de jogadores: id={jogo_id}")
        raise HTTPException(status_code=404, detail="Jogo não encontrado.")

    stats = (db.query(PlayerGameStats, Player).join(Player, PlayerGameStats.player_id == Player.id).filter(PlayerGameStats.game_id == jogo_id).all())

    lista_stats = []
    for stat_data in stats:
        stat = stat_data[0]
        jogador = stat_data[1]

        lista_stats.append({
            "jogador_id": stat.player_id,
            "nome_jogador": f"{jogador.firstname} {jogador.lastname}",
            "time_id": stat.team_id,
            "posicao": stat.pos,
            "minutos": stat.minutes,
            "pontos": stat.points,
            "assistencias": stat.assists,
            "rebotes_totais": stat.tot_reb,
            "rebotes_ofensivos": stat.off_reb,
            "rebotes_defensivos": stat.def_reb,
            "roubos": stat.steals,
            "bloqueios": stat.blocks,
            "turnovers": stat.turnovers,
            "faltas": stat.p_fouls,
            "fgm": stat.fgm, "fga": stat.fga, "fgp": float(stat.fgp) if stat.fgp is not None else None,
            "ftm": stat.ftm, "fta": stat.fta, "ftp": float(stat.ftp) if stat.ftp is not None else None,
            "tpm": stat.tpm, "tpa": stat.tpa, "tpp": float(stat.tpp) if stat.tpp is not None else None,
            "plus_minus": stat.plus_minus,
            "comentario": stat.comment,
        })
    return {"jogo_id": jogo_id, "total": len(lista_stats), "estatisticas": lista_stats}

@router.get("/jogadores")
def listar_jogadores(time_id: int = Query(None), temporada: int = Query(None), nome: str = Query(None), sobrenome: str = Query(None),
                     page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    logger.info(f"Listando jogadores — time_id={time_id}, temporada={temporada}")

    query = db.query(Player)

    if time_id is not None or temporada is not None:
        query = query.join(PlayerTeamSeason, PlayerTeamSeason.player_id == Player.id)
        if time_id is not None:
            query = query.filter(PlayerTeamSeason.team_id == time_id)
        if temporada is not None:
            query = query.filter(PlayerTeamSeason.season == temporada)
        query = query.distinct()

    if nome:
        query = query.filter(Player.firstname.ilike(f"%{nome}%"))
    if sobrenome:
        query = query.filter(Player.lastname.ilike(f"%{sobrenome}%"))

    total = query.count()
    offset = (page - 1) * page_size
    jogadores = query.order_by(Player.lastname.asc()).offset(offset).limit(page_size).all()

    lista_jogadores = []
    for jogador in jogadores:
        lista_jogadores.append({
            "id": jogador.id,
            "nome": jogador.firstname,
            "sobrenome": jogador.lastname,
            "data_nascimento": jogador.birth_date,
            "pais_nascimento": jogador.birth_country,
            "inicio_nba": jogador.nba_start,
            "altura_metros": float(jogador.height_meters) if jogador.height_meters is not None else None,
            "peso_kg": float(jogador.weight_kilograms) if jogador.weight_kilograms is not None else None,
            "faculdade": jogador.college,
        })
    return {"total": total, "pagina": page, "tamanho_pagina": page_size, "jogadores": lista_jogadores}

@router.get("/jogadores/{jogador_id}")
def obter_jogador(jogador_id: int, db: Session = Depends(get_db)):
    jogador = db.query(Player).filter(Player.id == jogador_id).first()
    if not jogador:
        logger.warning(f"Jogador não encontrado: id={jogador_id}")
        raise HTTPException(status_code=404, detail="Jogador não encontrado.")

    times_jogador = (db.query(PlayerTeamSeason, Team).join(Team, PlayerTeamSeason.team_id == Team.id)
                     .filter(PlayerTeamSeason.player_id == jogador_id).order_by(PlayerTeamSeason.season.desc()).all())

    historico_times = []
    for time_data in times_jogador:
        pts = time_data[0]
        time = time_data[1]
        historico_times.append({"temporada": pts.season, "time_id": pts.team_id, "nome_time": time.name, "camisa": pts.jersey, "posicao": pts.pos, "ativo": pts.active})

    return {
        "id": jogador.id,
        "nome": jogador.firstname,
        "sobrenome": jogador.lastname,
        "data_nascimento": jogador.birth_date,
        "pais_nascimento": jogador.birth_country,
        "inicio_nba": jogador.nba_start,
        "altura_pes": jogador.height_feet,
        "altura_polegadas": jogador.height_inches,
        "altura_metros": float(jogador.height_meters) if jogador.height_meters is not None else None,
        "peso_libras": jogador.weight_pounds,
        "peso_kg": float(jogador.weight_kilograms) if jogador.weight_kilograms is not None else None,
        "faculdade": jogador.college,
        "afiliacao": jogador.affiliation,
        "historico_times": historico_times,
    }

@router.get("/jogadores/{jogador_id}/estatisticas/temporada")
def estatisticas_temporada_jogador(jogador_id: int, temporada: int = Query(2023), db: Session = Depends(get_db), usuario_atual: dict = Depends(obter_usuario_atual)):
    jogador = db.query(Player).filter(Player.id == jogador_id).first()
    if not jogador:
        logger.warning(f"Jogador não encontrado ao buscar estatísticas de temporada: id={jogador_id}")
        raise HTTPException(status_code=404, detail="Jogador não encontrado.")

    stats = (db.query(PlayerGameStats).join(Game, PlayerGameStats.game_id == Game.id)
             .filter(PlayerGameStats.player_id == jogador_id, Game.season == temporada, Game.status_short == 3).all())

    if len(stats) == 0:
        return {"jogador_id": jogador_id, "nome_jogador": f"{jogador.firstname} {jogador.lastname}", "temporada": temporada, "mensagem": "Sem dados para esta temporada."}

    total_pontos = 0
    total_assistencias = 0
    total_rebotes = 0
    total_roubos = 0
    total_bloqueios = 0
    total_turnovers = 0
    lista_fgp = []
    lista_tpp = []
    lista_ftp = []

    for stat in stats:
        total_pontos = total_pontos + (stat.points or 0)
        total_assistencias = total_assistencias + (stat.assists or 0)
        total_rebotes = total_rebotes + (stat.tot_reb or 0)
        total_roubos = total_roubos + (stat.steals or 0)
        total_bloqueios = total_bloqueios + (stat.blocks or 0)
        total_turnovers = total_turnovers + (stat.turnovers or 0)
        if stat.fgp is not None:
            lista_fgp.append(float(stat.fgp))
        if stat.tpp is not None:
            lista_tpp.append(float(stat.tpp))
        if stat.ftp is not None:
            lista_ftp.append(float(stat.ftp))

    num_jogos = len(stats)

    if lista_fgp:
        media_fgp = round(sum(lista_fgp) / len(lista_fgp), 2) 
    else:
        media_fgp = 0
    
    if lista_tpp:
        media_tpp = round(sum(lista_tpp) / len(lista_tpp), 2) 
    else:
        media_tpp = 0
    
    if lista_ftp:
        media_ftp = round(sum(lista_ftp) / len(lista_ftp), 2) 
    else:
        media_ftp = 0

    return {
        "jogador_id": jogador_id,
        "nome_jogador": f"{jogador.firstname} {jogador.lastname}",
        "temporada": temporada,
        "jogos_disputados": num_jogos,
        "totais": {"pontos": total_pontos, "assistencias": total_assistencias, "rebotes": total_rebotes, "roubos": total_roubos, "bloqueios": total_bloqueios, "turnovers": total_turnovers},
        "medias": {
            "pontos": round(total_pontos / num_jogos, 2),
            "assistencias": round(total_assistencias / num_jogos, 2),
            "rebotes": round(total_rebotes / num_jogos, 2),
            "roubos": round(total_roubos / num_jogos, 2),
            "bloqueios": round(total_bloqueios / num_jogos, 2),
            "turnovers": round(total_turnovers / num_jogos, 2),
            "fg_pct": media_fgp,
            "three_pct": media_tpp,
            "ft_pct": media_ftp,
        },
    }

@router.get("/jogadores/{jogador_id}/estatisticas/jogos")
def estatisticas_jogos_jogador(jogador_id: int, temporada: int = Query(None), limite: int = Query(10, ge=1, le=100), db: Session = Depends(get_db), usuario_atual: dict = Depends(obter_usuario_atual)):
    jogador = db.query(Player).filter(Player.id == jogador_id).first()
    if not jogador:
        logger.warning(f"Jogador não encontrado ao buscar histórico de jogos: id={jogador_id}")
        raise HTTPException(status_code=404, detail="Jogador não encontrado.")

    query = (db.query(PlayerGameStats, Game).join(Game, PlayerGameStats.game_id == Game.id).filter(PlayerGameStats.player_id == jogador_id))

    if temporada:
        query = query.filter(Game.season == temporada)

    stats = query.order_by(Game.date_start.desc()).limit(limite).all()

    lista_jogos = []
    for stat_data in stats:
        stat = stat_data[0]
        jogo = stat_data[1]

        if stat.team_id == jogo.home_team_id:
            adversario_id = jogo.away_team_id 
        else:
            adversario_id = jogo.home_team_id

        lista_jogos.append({
            "jogo_id": stat.game_id,
            "data": jogo.date_start,
            "temporada": jogo.season,
            "adversario_id": adversario_id,
            "minutos": stat.minutes,
            "pontos": stat.points,
            "assistencias": stat.assists,
            "rebotes": stat.tot_reb,
            "roubos": stat.steals,
            "bloqueios": stat.blocks,
            "turnovers": stat.turnovers,
            "fg_pct": float(stat.fgp) if stat.fgp is not None else None,
            "three_pct": float(stat.tpp) if stat.tpp is not None else None,
            "ft_pct": float(stat.ftp) if stat.ftp is not None else None,
            "plus_minus": stat.plus_minus,
        })
    return {"jogador_id": jogador_id, "nome_jogador": f"{jogador.firstname} {jogador.lastname}", "total": len(lista_jogos), "jogos": lista_jogos}

@router.get("/jogadores/{jogador_id}/estatisticas/ultimos-jogos")
def estatisticas_ultimos_n_jogos(jogador_id: int, n_jogos: int = Query(10, description="5, 10, 15 ou 20"), temporada: int = Query(None), db: Session = Depends(get_db), usuario_atual: dict = Depends(obter_usuario_atual)):
    jogador = db.query(Player).filter(Player.id == jogador_id).first()
    if not jogador:
        logger.warning(f"Jogador não encontrado ao buscar últimos jogos: id={jogador_id}")
        raise HTTPException(status_code=404, detail="Jogador não encontrado.")

    valores_permitidos = [5, 10, 15, 20]
    if n_jogos not in valores_permitidos:
        raise HTTPException(status_code=400, detail=f"n_jogos deve ser um dos valores: {valores_permitidos}")

    query = (db.query(PlayerGameStats, Game).join(Game, PlayerGameStats.game_id == Game.id)
             .filter(PlayerGameStats.player_id == jogador_id, Game.status_short == 3))

    if temporada:
        query = query.filter(Game.season == temporada)

    stats = query.order_by(Game.date_start.desc()).limit(n_jogos).all()

    if len(stats) == 0:
        return {"jogador_id": jogador_id, "nome_jogador": f"{jogador.firstname} {jogador.lastname}", "n_jogos": n_jogos, "mensagem": "Sem dados para calcular."}

    total_pontos = 0
    total_assistencias = 0
    total_rebotes = 0
    total_roubos = 0
    total_bloqueios = 0
    total_turnovers = 0
    total_fgm = 0
    total_fga = 0
    total_tpm = 0
    total_tpa = 0
    total_ftm = 0
    total_fta = 0
    lista_jogos = []

    for stat_data in stats:
        stat = stat_data[0]
        jogo = stat_data[1]

        total_pontos = total_pontos + (stat.points or 0)
        total_assistencias = total_assistencias + (stat.assists or 0)
        total_rebotes = total_rebotes + (stat.tot_reb or 0)
        total_roubos = total_roubos + (stat.steals or 0)
        total_bloqueios = total_bloqueios + (stat.blocks or 0)
        total_turnovers = total_turnovers + (stat.turnovers or 0)
        total_fgm = total_fgm + (stat.fgm or 0)
        total_fga = total_fga + (stat.fga or 0)
        total_tpm = total_tpm + (stat.tpm or 0)
        total_tpa = total_tpa + (stat.tpa or 0)
        total_ftm = total_ftm + (stat.ftm or 0)
        total_fta = total_fta + (stat.fta or 0)

        lista_jogos.append({"jogo_id": jogo.id, "data": jogo.date_start, "pontos": stat.points, "assistencias": stat.assists, "rebotes": stat.tot_reb})

    num_jogos = len(stats)

    if total_fga > 0:
        fg_pct = round((total_fgm / total_fga) * 100, 2) 
    else:
        fg_pct = 0
    if total_tpa > 0:
        three_pct = round((total_tpm / total_tpa) * 100, 2) 
    else:
        three_pct = 0
        
    if total_fta > 0:
        ft_pct = round((total_ftm / total_fta) * 100, 2)
    else:
        ft_pct = 0

    return {
        "jogador_id": jogador_id,
        "nome_jogador": f"{jogador.firstname} {jogador.lastname}",
        "n_jogos": n_jogos,
        "jogos_analisados": num_jogos,
        "temporada": temporada,
        "medias": {
            "pontos": round(total_pontos / num_jogos, 2),
            "assistencias": round(total_assistencias / num_jogos, 2),
            "rebotes": round(total_rebotes / num_jogos, 2),
            "roubos": round(total_roubos / num_jogos, 2),
            "bloqueios": round(total_bloqueios / num_jogos, 2),
            "turnovers": round(total_turnovers / num_jogos, 2),
            "fg_pct": fg_pct,
            "three_pct": three_pct,
            "ft_pct": ft_pct,
        },
        "jogos": lista_jogos,
    }

@router.get("/jogadores/{jogador_id}/estatisticas/casa-fora")
def estatisticas_casa_fora(jogador_id: int, temporada: int = Query(2023), local: str = Query(..., description="casa ou fora"), db: Session = Depends(get_db), usuario_atual: dict = Depends(obter_usuario_atual)):
    jogador = db.query(Player).filter(Player.id == jogador_id).first()
    if not jogador:
        logger.warning(f"Jogador não encontrado ao buscar stats casa/fora: id={jogador_id}")
        raise HTTPException(status_code=404, detail="Jogador não encontrado.")

    if local not in ["casa", "fora"]:
        raise HTTPException(status_code=400, detail="local deve ser 'casa' ou 'fora'.")

    buscar_casa = local == "casa"

    stats_query = (db.query(PlayerGameStats, Game, GameTeamScore)
                   .join(Game, PlayerGameStats.game_id == Game.id)
                   .join(GameTeamScore, and_(GameTeamScore.game_id == Game.id, GameTeamScore.team_id == PlayerGameStats.team_id))
                   .filter(PlayerGameStats.player_id == jogador_id, Game.season == temporada, Game.status_short == 3, GameTeamScore.is_home == buscar_casa).all())

    if len(stats_query) == 0:
        return {"jogador_id": jogador_id, "nome_jogador": f"{jogador.firstname} {jogador.lastname}", "temporada": temporada, "local": local, "mensagem": f"Sem dados para jogos {local}."}

    total_pontos = 0
    total_assistencias = 0
    total_rebotes = 0
    total_roubos = 0
    total_bloqueios = 0
    total_turnovers = 0
    total_fgm = 0
    total_fga = 0
    total_tpm = 0
    total_tpa = 0
    total_ftm = 0
    total_fta = 0
    lista_jogos = []

    for stat_data in stats_query:
        stat = stat_data[0]
        jogo = stat_data[1]

        total_pontos = total_pontos + (stat.points or 0)
        total_assistencias = total_assistencias + (stat.assists or 0)
        total_rebotes = total_rebotes + (stat.tot_reb or 0)
        total_roubos = total_roubos + (stat.steals or 0)
        total_bloqueios = total_bloqueios + (stat.blocks or 0)
        total_turnovers = total_turnovers + (stat.turnovers or 0)
        total_fgm = total_fgm + (stat.fgm or 0)
        total_fga = total_fga + (stat.fga or 0)
        total_tpm = total_tpm + (stat.tpm or 0)
        total_tpa = total_tpa + (stat.tpa or 0)
        total_ftm = total_ftm + (stat.ftm or 0)
        total_fta = total_fta + (stat.fta or 0)

        lista_jogos.append({"jogo_id": jogo.id, "data": jogo.date_start, "pontos": stat.points, "assistencias": stat.assists, "rebotes": stat.tot_reb})

    num_jogos = len(stats_query)

    if total_fga > 0:
        fg_pct = round((total_fgm / total_fga) * 100, 2)
    else:
        fg_pct = 0
        
    if total_tpa > 0:
        three_pct = round((total_tpm / total_tpa) * 100, 2) 
    else:
        three_pct = 0
    if total_fta > 0:
        ft_pct = round((total_ftm / total_fta) * 100, 2) 
    else:
        ft_pct = 0

    return {
        "jogador_id": jogador_id,
        "nome_jogador": f"{jogador.firstname} {jogador.lastname}",
        "temporada": temporada,
        "local": local,
        "jogos_disputados": num_jogos,
        "medias": {
            "pontos": round(total_pontos / num_jogos, 2),
            "assistencias": round(total_assistencias / num_jogos, 2),
            "rebotes": round(total_rebotes / num_jogos, 2),
            "roubos": round(total_roubos / num_jogos, 2),
            "bloqueios": round(total_bloqueios / num_jogos, 2),
            "turnovers": round(total_turnovers / num_jogos, 2),
            "fg_pct": fg_pct,
            "three_pct": three_pct,
            "ft_pct": ft_pct,
        },
        "jogos": lista_jogos,
    }

@router.get("/analiticos/maiores-pontuadores")
def maiores_pontuadores(temporada: int = Query(2023), limite: int = Query(10, ge=1, le=50), db: Session = Depends(get_db), usuario_atual: dict = Depends(obter_usuario_atual)):
    logger.info(f"Consultando maiores pontuadores — temporada={temporada}, limite={limite}")

    resultados = (db.query(
        Player.id,
        Player.firstname,
        Player.lastname,
        func.count(PlayerGameStats.game_id).label("jogos"),
        func.sum(PlayerGameStats.points).label("total_pontos"),
        func.avg(PlayerGameStats.points).label("media_pontos"),
    )
    .join(PlayerGameStats, Player.id == PlayerGameStats.player_id)
    .join(Game, PlayerGameStats.game_id == Game.id)
    .filter(Game.season == temporada, Game.status_short == 3)
    .group_by(Player.id, Player.firstname, Player.lastname)
    .order_by(desc("media_pontos"))
    .limit(limite)
    .all())

    lista = []
    for r in resultados:
        lista.append({
            "jogador_id": r.id,
            "nome_jogador": f"{r.firstname} {r.lastname}",
            "jogos_disputados": r.jogos,
            "total_pontos": r.total_pontos,
            "media_pontos": round(float(r.media_pontos), 2),
        })

    return {"temporada": temporada, "total": len(lista), "maiores_pontuadores": lista}

@router.get("/analiticos/tendencias-time/{time_id}")
def tendencias_time(time_id: int, temporada: int = Query(2023), ultimos_n_jogos: int = Query(10, ge=1, le=20), db: Session = Depends(get_db), usuario_atual: dict = Depends(obter_usuario_atual)):
    time = db.query(Team).filter(Team.id == time_id).first()
    if not time:
        logger.warning(f"Time não encontrado ao buscar tendências: id={time_id}")
        raise HTTPException(status_code=404, detail="Time não encontrado.")

    jogos = (db.query(Game, GameTeamScore).join(GameTeamScore, GameTeamScore.game_id == Game.id)
             .filter(Game.season == temporada, GameTeamScore.team_id == time_id, Game.status_short == 3)
             .order_by(Game.date_start.desc()).limit(ultimos_n_jogos).all())

    if len(jogos) == 0:
        return {"time_id": time_id, "nome_time": time.name, "mensagem": "Sem jogos finalizados."}

    vitorias = 0
    pontos_feitos = []
    pontos_sofridos = []

    for jogo_data in jogos:
        jogo = jogo_data[0]
        score = jogo_data[1]

        adversario = db.query(GameTeamScore).filter(GameTeamScore.game_id == jogo.id, GameTeamScore.team_id != time_id).first()
        if adversario:
            if score.points is not None:
                pts_feitos = score.points 
            else:
                pts_feitos = 0
            if adversario.points is not None:
                pts_sofridos = adversario.points
            else:
                pts_sofridos = 0

            pontos_feitos.append(pts_feitos)
            pontos_sofridos.append(pts_sofridos)

            if pts_feitos > pts_sofridos:
                vitorias = vitorias + 1

    num_jogos = len(pontos_feitos)
    derrotas = num_jogos - vitorias
    if num_jogos > 0:
        aproveitamento = round(vitorias / num_jogos * 100, 2) 
    else:
        aproveitamento = 0
    if num_jogos > 0:
        media_feitos = round(sum(pontos_feitos) / num_jogos, 2)
    else:
        media_feitos = 0
    if num_jogos > 0:
        media_sofridos = round(sum(pontos_sofridos) / num_jogos, 2) 
    else:
        media_sofridos = 0
    if num_jogos > 0:
        diferencial = round((sum(pontos_feitos) - sum(pontos_sofridos)) / num_jogos, 2)
    else:
        diferencial = 0

    tendencia_ofensiva = "estavel"
    if len(pontos_feitos) >= 3:
        if pontos_feitos[0] > pontos_feitos[-1]:
            tendencia_ofensiva = "melhorando"     
        else:
            tendencia_ofensiva = "piorando"

    tendencia_defensiva = "estavel"
    if len(pontos_sofridos) >= 3:
        if pontos_sofridos[0] < pontos_sofridos[-1]:
            tendencia_defensiva = "melhorando" 
        else:
            tendencia_defensiva = "piorando"
    return {
        "time_id": time_id,
        "nome_time": time.name,
        "temporada": temporada,
        "ultimos_n_jogos": num_jogos,
        "record": f"{vitorias}-{derrotas}",
        "aproveitamento": aproveitamento,
        "media_pontos_feitos": media_feitos,
        "media_pontos_sofridos": media_sofridos,
        "diferencial_pontos": diferencial,
        "tendencia_ofensiva": tendencia_ofensiva,
        "tendencia_defensiva": tendencia_defensiva,
    }