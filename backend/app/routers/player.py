import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.db.db_utils import get_db
from app.db.models import (
    Game,
    GameTeamScore,
    Player,
    PlayerGameStats,
    PlayerTeamSeason,
    Team,
)
from app.routers.auth import obter_usuario_atual
from app.schemas.player import (
    EstatisticasCasaForaResponse,
    EstatisticasJogosResponse,
    EstatisticasTemporadaResponse,
    EstatisticasUltimosJogosResponse,
    PlayerListResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=PlayerListResponse)
def listar_jogadores(
    time_id: int = Query(None),
    temporada: int = Query(None),
    nome: str = Query(None),
    sobrenome: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    stmt = select(Player)

    if time_id is not None or temporada is not None:
        stmt = stmt.join(PlayerTeamSeason, PlayerTeamSeason.player_id == Player.id)
        if time_id is not None:
            stmt = stmt.where(PlayerTeamSeason.team_id == time_id)
        if temporada is not None:
            stmt = stmt.where(PlayerTeamSeason.season == temporada)
        stmt = stmt.distinct()

    if nome:
        stmt = stmt.where(Player.firstname.ilike(f"%{nome}%"))
    if sobrenome:
        stmt = stmt.where(Player.lastname.ilike(f"%{sobrenome}%"))

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar()
    offset = (page - 1) * page_size
    jogadores = (
        db.execute(stmt.order_by(Player.lastname.asc()).offset(offset).limit(page_size))
        .scalars()
        .all()
    )

    lista_jogadores = []
    for jogador in jogadores:
        lista_jogadores.append(
            {
                "id": jogador.id,
                "nome": jogador.firstname,
                "sobrenome": jogador.lastname,
                "data_nascimento": jogador.birth_date,
                "pais_nascimento": jogador.birth_country,
                "inicio_nba": jogador.nba_start,
                "altura_metros": float(jogador.height_meters)  # type: ignore
                if jogador.height_meters is not None
                else None,
                "peso_kg": float(jogador.weight_kilograms)  # type: ignore
                if jogador.weight_kilograms is not None
                else None,
                "faculdade": jogador.college,
            }
        )

    return {
        "total": total,
        "pagina": page,
        "tamanho_pagina": page_size,
        "jogadores": lista_jogadores,
    }


@router.get("/{jogador_id}")
def obter_jogador(jogador_id: int, db: Session = Depends(get_db)):
    jogador = db.execute(
        select(Player).where(Player.id == jogador_id)
    ).scalar_one_or_none()
    if not jogador:
        logger.warning(f"Jogador nao encontrado: id={jogador_id}")
        raise HTTPException(status_code=404, detail="Jogador não encontrado.")

    stmt = (
        select(PlayerTeamSeason, Team)
        .join(Team, PlayerTeamSeason.team_id == Team.id)
        .where(PlayerTeamSeason.player_id == jogador_id)
    )
    times_jogador = db.execute(stmt).all()

    historico_times_raw = []
    for time_data in times_jogador:
        pts = time_data[0]
        time = time_data[1]

        stmt_jogo = (
            select(Game.date_start)
            .join(PlayerGameStats, PlayerGameStats.game_id == Game.id)
            .where(
                PlayerGameStats.player_id == jogador_id,
                PlayerGameStats.team_id == pts.team_id,
                Game.season == pts.season,
            )
            .order_by(Game.date_start.asc())
        )
        primeiro_jogo = db.execute(stmt_jogo).first()

        data_ingresso = None
        mes_ingresso = None
        if primeiro_jogo and primeiro_jogo[0]:
            data_ingresso = primeiro_jogo[0]
            mes_ingresso = primeiro_jogo[0].strftime("%m/%Y")

        historico_times_raw.append(
            {
                "temporada": pts.season,
                "time_id": pts.team_id,
                "nome_time": time.name,
                "camisa": pts.jersey,
                "posicao": pts.pos,
                "ativo": pts.active,
                "mes_ingresso": mes_ingresso,
                "_data_sort": data_ingresso,
            }
        )

    historico_times_raw.sort(
        key=lambda x: (x["_data_sort"] is None, x["_data_sort"] or x["temporada"])
    )

    historico_times = []
    for item in historico_times_raw:
        historico_times.append(
            {
                "temporada": item["temporada"],
                "time_id": item["time_id"],
                "nome_time": item["nome_time"],
                "camisa": item["camisa"],
                "posicao": item["posicao"],
                "ativo": item["ativo"],
                "mes_ingresso": item["mes_ingresso"],
            }
        )

    return {
        "id": jogador.id,
        "nome": jogador.firstname,
        "sobrenome": jogador.lastname,
        "data_nascimento": jogador.birth_date,
        "pais_nascimento": jogador.birth_country,
        "inicio_nba": jogador.nba_start,
        "altura_pes": jogador.height_feet,
        "altura_polegadas": jogador.height_inches,
        "altura_metros": float(jogador.height_meters)  # type: ignore
        if jogador.height_meters is not None
        else None,
        "peso_libras": jogador.weight_pounds,
        "peso_kg": float(jogador.weight_kilograms)  # type: ignore
        if jogador.weight_kilograms is not None
        else None,
        "faculdade": jogador.college,
        "afiliacao": jogador.affiliation,
        "historico_times": historico_times,
    }


@router.get(
    "/{jogador_id}/estatisticas/temporada", response_model=EstatisticasTemporadaResponse
)
def estatisticas_temporada_jogador(
    jogador_id: int, temporada: int = Query(2025), db: Session = Depends(get_db)
):
    jogador = db.execute(
        select(Player).where(Player.id == jogador_id)
    ).scalar_one_or_none()
    if not jogador:
        logger.warning(
            f"Jogador nao encontrado ao buscar estatisticas de temporada: id={jogador_id}"
        )
        raise HTTPException(status_code=404, detail="Jogador não encontrado.")

    stmt = (
        select(PlayerGameStats)
        .join(Game, PlayerGameStats.game_id == Game.id)
        .where(
            PlayerGameStats.player_id == jogador_id,
            Game.season == temporada,
            Game.status_short == 3,
        )
    )
    stats = db.execute(stmt).scalars().all()

    if len(stats) == 0:
        return {
            "jogador_id": jogador_id,
            "nome_jogador": f"{jogador.firstname} {jogador.lastname}",
            "temporada": temporada,
            "mensagem": "Sem dados para esta temporada.",
        }

    total_pontos = 0
    total_assistencias = 0
    total_rebotes = 0
    total_roubos = 0
    total_bloqueios = 0
    total_turnovers = 0
    total_plus_minus = 0
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
        total_plus_minus = total_plus_minus + (stat.plus_minus or 0)
        if stat.fgp is not None:
            lista_fgp.append(float(stat.fgp))  # type: ignore
        if stat.tpp is not None:
            lista_tpp.append(float(stat.tpp))  # type: ignore
        if stat.ftp is not None:
            lista_ftp.append(float(stat.ftp))  # type: ignore

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
        "totais": {
            "pontos": total_pontos,
            "assistencias": total_assistencias,
            "rebotes": total_rebotes,
            "roubos": total_roubos,
            "bloqueios": total_bloqueios,
            "turnovers": total_turnovers,
        },
        "medias": {
            "pontos": round(total_pontos / num_jogos, 2),  # type: ignore
            "assistencias": round(total_assistencias / num_jogos, 2),  # type: ignore
            "rebotes": round(total_rebotes / num_jogos, 2),  # type: ignore
            "roubos": round(total_roubos / num_jogos, 2),  # type: ignore
            "bloqueios": round(total_bloqueios / num_jogos, 2),  # type: ignore
            "turnovers": round(total_turnovers / num_jogos, 2),  # type: ignore
            "plus_minus": round(total_plus_minus / num_jogos, 2),  # type: ignore
            "fg_pct": media_fgp,
            "three_pct": media_tpp,
            "ft_pct": media_ftp,
        },
    }


@router.get(
    "/{jogador_id}/estatisticas/jogos", response_model=EstatisticasJogosResponse
)
def estatisticas_jogos_jogador(
    jogador_id: int,
    temporada: int = Query(None),
    limite: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    usuario_atual=Depends(obter_usuario_atual),
):
    jogador = db.execute(
        select(Player).where(Player.id == jogador_id)
    ).scalar_one_or_none()
    if not jogador:
        logger.warning(
            f"Jogador nao encontrado ao buscar historico de jogos: id={jogador_id}"
        )
        raise HTTPException(status_code=404, detail="Jogador não encontrado.")

    stmt = (
        select(PlayerGameStats, Game)
        .join(Game, PlayerGameStats.game_id == Game.id)
        .where(PlayerGameStats.player_id == jogador_id)
    )

    if temporada:
        stmt = stmt.where(Game.season == temporada)

    stmt = stmt.order_by(Game.date_start.desc()).limit(limite)
    stats = db.execute(stmt).all()

    lista_jogos = []
    for stat_data in stats:
        stat = stat_data[0]
        jogo = stat_data[1]

        if stat.team_id == jogo.home_team_id:
            adversario_id = jogo.away_team_id
        else:
            adversario_id = jogo.home_team_id

        lista_jogos.append(
            {
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
            }
        )

    return {
        "jogador_id": jogador_id,
        "nome_jogador": f"{jogador.firstname} {jogador.lastname}",
        "total": len(lista_jogos),
        "jogos": lista_jogos,
    }


@router.get(
    "/{jogador_id}/estatisticas/ultimos-jogos",
    response_model=EstatisticasUltimosJogosResponse,
)
def estatisticas_ultimos_n_jogos(
    jogador_id: int,
    n_jogos: int = Query(None, description="Limite de jogos. Omitir = todos os jogos"),
    temporada: int = Query(None),
    db: Session = Depends(get_db),
):
    jogador = db.execute(
        select(Player).where(Player.id == jogador_id)
    ).scalar_one_or_none()
    if not jogador:
        logger.warning(
            f"Jogador nao encontrado ao buscar ultimos jogos: id={jogador_id}"
        )
        raise HTTPException(status_code=404, detail="Jogador não encontrado.")

    stmt = (
        select(PlayerGameStats, Game)
        .join(Game, PlayerGameStats.game_id == Game.id)
        .where(PlayerGameStats.player_id == jogador_id, Game.status_short == 3)
    )

    if temporada:
        stmt = stmt.where(Game.season == temporada)

    stmt = stmt.order_by(Game.date_start.desc())
    if n_jogos is not None:
        stmt = stmt.limit(n_jogos)

    stats = db.execute(stmt).all()

    if len(stats) == 0:
        return {
            "jogador_id": jogador_id,
            "nome_jogador": f"{jogador.firstname} {jogador.lastname}",
            "n_jogos": n_jogos or 0,
            "jogos_analisados": 0,
            "temporada": temporada,
            "medias": None,
            "jogos": [],
            "mensagem": "Sem dados para calcular.",
        }

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

        if stat.team_id == jogo.home_team_id:
            adversario_id = jogo.away_team_id
        else:
            adversario_id = jogo.home_team_id

        time_adversario = db.execute(
            select(Team).where(Team.id == adversario_id)
        ).scalar_one_or_none()
        if time_adversario:
            nome_adversario = time_adversario.name
        else:
            nome_adversario = "—"

        fg_pct_jogo = round(float(stat.fgp), 1) if stat.fgp is not None else None
        three_pct_jogo = round(float(stat.tpp), 1) if stat.tpp is not None else None
        ft_pct_jogo = round(float(stat.ftp), 1) if stat.ftp is not None else None

        em_casa = stat.team_id == jogo.home_team_id

        lista_jogos.append(
            {
                "jogo_id": jogo.id,
                "data": jogo.date_start,
                "adversario_id": adversario_id,
                "adversario": nome_adversario,
                "em_casa": em_casa,
                "pontos": stat.points,
                "assistencias": stat.assists,
                "rebotes": stat.tot_reb,
                "roubos": stat.steals,
                "bloqueios": stat.blocks,
                "turnovers": stat.turnovers,
                "minutos": stat.minutes,
                "fg_pct": fg_pct_jogo,
                "three_pct": three_pct_jogo,
                "ft_pct": ft_pct_jogo,
                "plus_minus": stat.plus_minus,
            }
        )

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
        "n_jogos": n_jogos or 0,
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


@router.get(
    "/{jogador_id}/estatisticas/casa-fora", response_model=EstatisticasCasaForaResponse
)
def estatisticas_casa_fora(
    jogador_id: int,
    temporada: int = Query(None),
    local: str = Query(..., description="casa ou fora"),
    db: Session = Depends(get_db),
):
    jogador = db.execute(
        select(Player).where(Player.id == jogador_id)
    ).scalar_one_or_none()
    if not jogador:
        logger.warning(
            f"Jogador nao encontrado ao buscar stats casa/fora: id={jogador_id}"
        )
        raise HTTPException(status_code=404, detail="Jogador não encontrado.")

    if local not in ["casa", "fora"]:
        raise HTTPException(status_code=400, detail="local deve ser 'casa' ou 'fora'.")

    buscar_casa = local == "casa"

    stmt = (
        select(PlayerGameStats, Game, GameTeamScore)
        .join(Game, PlayerGameStats.game_id == Game.id)
        .join(
            GameTeamScore,
            and_(
                GameTeamScore.game_id == Game.id,
                GameTeamScore.team_id == PlayerGameStats.team_id,
            ),
        )
        .where(
            PlayerGameStats.player_id == jogador_id,
            Game.season == temporada,
            Game.status_short == 3,
            GameTeamScore.is_home == buscar_casa,
        )
    )

    stats_query = db.execute(stmt).all()

    if len(stats_query) == 0:
        return {
            "jogador_id": jogador_id,
            "nome_jogador": f"{jogador.firstname} {jogador.lastname}",
            "temporada": temporada,
            "local": local,
            "mensagem": f"Sem dados para jogos {local}.",
        }

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

        lista_jogos.append(
            {
                "jogo_id": jogo.id,
                "data": jogo.date_start,
                "pontos": stat.points,
                "assistencias": stat.assists,
                "rebotes": stat.tot_reb,
                "roubos": stat.steals,
                "bloqueios": stat.blocks,
                "turnovers": stat.turnovers,
            }
        )

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
