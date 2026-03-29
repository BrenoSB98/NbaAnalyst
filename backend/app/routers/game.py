import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.db_utils import get_db
from app.db.models import Game, GameTeamScore, GameTeamStats, Player, PlayerGameStats, Team
from app.schemas.game import EstatisticasJogadoresJogoResponse, EstatisticasTimesJogoResponse, GameDetalheResponse, GameListResponse, ProximosJogosResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("", response_model=GameListResponse)
def listar_jogos(temporada: int = Query(None), time_id: int = Query(None), data_inicio: str = Query(None), data_fim: str = Query(None),
                 status: int = Query(None), page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
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

    return {
        "total": total, 
        "pagina": page, 
        "tamanho_pagina": page_size, 
        "jogos": lista_jogos
        }

@router.get("/contagem-hoje")
def contar_jogos_hoje(db: Session = Depends(get_db)):
    fuso_sp = ZoneInfo("America/Sao_Paulo")
    agora_sp = datetime.now(fuso_sp)
    inicio_sp = agora_sp.replace(hour=10, minute=0, second=0, microsecond=0)
    fim_sp = agora_sp.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1, hours=2)
 
    inicio_utc = inicio_sp.astimezone(timezone.utc)
    fim_utc = fim_sp.astimezone(timezone.utc)
 
    total = db.query(Game).filter(
        Game.date_start >= inicio_utc,
        Game.date_start < fim_utc
    ).count()
 
    return {"total_jogos": total}

@router.get("/proximos", response_model=ProximosJogosResponse)
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

        if time_casa:
            nome_casa = time_casa.name     
        else:
            nome_casa = None
        if time_fora:
            nome_fora = time_fora.name     
        else:
            nome_fora = None

        lista_jogos.append({
            "id": jogo.id,
            "data_inicio": jogo.date_start,
            "time_casa": {
                "id": jogo.home_team_id,
                "nome": nome_casa
            },
            "time_fora": {
                "id": jogo.away_team_id,
                "nome": nome_fora
            },
            "arena": jogo.arena_name,
        })

    return {
        "total": len(lista_jogos),
        "dias": dias,
        "jogos": lista_jogos
    }

@router.get("/{jogo_id}", response_model=GameDetalheResponse)
def obter_jogo(jogo_id: int, db: Session = Depends(get_db)):
    jogo = db.query(Game).filter(Game.id == jogo_id).first()
    if not jogo:
        logger.warning(f"Jogo não encontrado: id={jogo_id}")
        raise HTTPException(status_code=404, detail="Jogo não encontrado.")

    scores = db.query(GameTeamScore).filter(GameTeamScore.game_id == jogo_id).all()

    info_casa = {
        "id": jogo.home_team_id, 
        "nome": None, 
        "apelido": None, 
        "logo": None, 
        "pontos": None, 
        "parciais": None
        }
    info_fora = {
        "id": jogo.away_team_id, 
        "nome": None, 
        "apelido": None, 
        "logo": None, 
        "pontos": None, 
        "parciais": None
        }

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
        parciais = {
            "q1": score.linescore_q1,
            "q2": score.linescore_q2,
            "q3": score.linescore_q3,
            "q4": score.linescore_q4
        }
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
        "arena": {
            "nome": jogo.arena_name, 
            "cidade": jogo.arena_city, 
            "estado": jogo.arena_state, 
            "pais": jogo.arena_country
            },
        "time_casa": info_casa,
        "time_fora": info_fora,
        "empates": jogo.times_tied,
        "mudancas_lideranca": jogo.lead_changes,
        "nugget": jogo.nugget,
    }

@router.get("/{jogo_id}/estatisticas-times", response_model=EstatisticasTimesJogoResponse)
def estatisticas_times_jogo(jogo_id: int, db: Session = Depends(get_db)):
    jogo = db.query(Game).filter(Game.id == jogo_id).first()
    if not jogo:
        logger.warning(f"Jogo não encontrado ao buscar estatísticas de times: id={jogo_id}")
        raise HTTPException(status_code=404, detail="Jogo não encontrado.")

    stats = db.query(GameTeamStats).filter(GameTeamStats.game_id == jogo_id).all()

    lista_stats = []
    for stat in stats:
        time = db.query(Team).filter(Team.id == stat.team_id).first()

        if time:
            nome_time = time.name
        else:
            nome_time = None

        lista_stats.append({
            "time_id": stat.team_id,
            "nome_time": nome_time,
            "pontos": stat.points,
            "fgm": stat.fgm,
            "fga": stat.fga,
            "fgp": float(stat.fgp) if stat.fgp is not None else None,
            "ftm": stat.ftm,
            "fta": stat.fta,
            "ftp": float(stat.ftp) if stat.ftp is not None else None,
            "tpm": stat.tpm,
            "tpa": stat.tpa,
            "tpp": float(stat.tpp) if stat.tpp is not None else None,
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

    return {
        "jogo_id": jogo_id,
        "estatisticas_times": lista_stats
    }

@router.get("/{jogo_id}/estatisticas-jogadores", response_model=EstatisticasJogadoresJogoResponse)
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
            "fgm": stat.fgm,
            "fga": stat.fga,
            "fgp": float(stat.fgp) if stat.fgp is not None else None,
            "ftm": stat.ftm,
            "fta": stat.fta,
            "ftp": float(stat.ftp) if stat.ftp is not None else None,
            "tpm": stat.tpm,
            "tpa": stat.tpa,
            "tpp": float(stat.tpp) if stat.tpp is not None else None,
            "plus_minus": stat.plus_minus,
            "comentario": stat.comment,
        })

    return {
        "jogo_id": jogo_id, 
        "total": len(lista_stats), 
        "estatisticas": lista_stats
        }