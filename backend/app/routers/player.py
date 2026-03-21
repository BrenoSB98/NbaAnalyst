import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.db.db_utils import get_db
from app.db.models import Game, GameTeamScore, Player, PlayerGameStats, PlayerTeamSeason, Team
from app.routers.auth import obter_usuario_atual
from app.schemas.player import EstatisticasCasaForaResponse, EstatisticasJogosResponse, EstatisticasTemporadaResponse, EstatisticasUltimosJogosResponse, PlayerDetalheResponse, PlayerListResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=PlayerListResponse)
def listar_jogadores(time_id: int = Query(None), temporada: int = Query(None), nome: str = Query(None), sobrenome: str = Query(None), page: int = Query(1, ge=1),
                     page_size: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
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

@router.get("/{jogador_id}", response_model=PlayerDetalheResponse)
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

@router.get("/{jogador_id}/estatisticas/temporada", response_model=EstatisticasTemporadaResponse)
def estatisticas_temporada_jogador(jogador_id: int, temporada: int = Query(2023), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
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

@router.get("/{jogador_id}/estatisticas/jogos", response_model=EstatisticasJogosResponse)
def estatisticas_jogos_jogador(jogador_id: int, temporada: int = Query(None), limite: int = Query(10, ge=1, le=100), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
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

    return {
        "jogador_id": jogador_id, 
        "nome_jogador": f"{jogador.firstname} {jogador.lastname}", 
        "total": len(lista_jogos), 
        "jogos": lista_jogos
        }

@router.get("/{jogador_id}/estatisticas/ultimos-jogos", response_model=EstatisticasUltimosJogosResponse)
def estatisticas_ultimos_n_jogos(jogador_id: int, n_jogos: int = Query(10, description="5, 10, 15 ou 20"), temporada: int = Query(None), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    jogador = db.query(Player).filter(Player.id == jogador_id).first()
    if not jogador:
        logger.warning(f"Jogador não encontrado ao buscar últimos jogos: id={jogador_id}")
        raise HTTPException(status_code=404, detail="Jogador não encontrado.")

    valores_permitidos = [5, 10, 15, 20, 40, 50] 
    if n_jogos not in valores_permitidos:
        raise HTTPException(status_code=400, detail=f"n_jogos deve ser um dos valores: {valores_permitidos}")

    query = (db.query(PlayerGameStats, Game).join(Game, PlayerGameStats.game_id == Game.id)
             .filter(PlayerGameStats.player_id == jogador_id, Game.status_short == 3))

    if temporada:
        query = query.filter(Game.season == temporada)

    stats = query.order_by(Game.date_start.desc()).limit(n_jogos).all()

    if len(stats) == 0:
        return {
            "jogador_id": jogador_id, 
            "nome_jogador": f"{jogador.firstname} {jogador.lastname}", 
            "n_jogos": n_jogos, 
            "jogos_analisados": 0, 
            "temporada": temporada, 
            "medias": None, 
            "jogos": [], 
            "mensagem": "Sem dados para calcular."
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

        # Busca o nome do time adversário para exibir na tabela
        if stat.team_id == jogo.home_team_id:
            adversario_id = jogo.away_team_id
        else:
            adversario_id = jogo.home_team_id

        time_adversario = db.query(Team).filter(Team.id == adversario_id).first()
        nome_adversario = time_adversario.name if time_adversario else "—"

        fg_pct_jogo = 0.0
        if (stat.fga or 0) > 0:
            fg_pct_jogo = round(((stat.fgm or 0) / stat.fga) * 100, 1)

        three_pct_jogo = 0.0
        if (stat.tpa or 0) > 0:
            three_pct_jogo = round(((stat.tpm or 0) / stat.tpa) * 100, 1)

        lista_jogos.append({
            "jogo_id": jogo.id,
            "data": jogo.date_start,
            "adversario_id": adversario_id,
            "adversario": nome_adversario,
            "pontos": stat.points,
            "assistencias": stat.assists,
            "rebotes": stat.tot_reb,
            "roubos": stat.steals,
            "bloqueios": stat.blocks,
            "turnovers": stat.turnovers,
            "minutos": stat.minutes,
            "fg_pct": fg_pct_jogo,
            "three_pct": three_pct_jogo,
            "plus_minus": stat.plus_minus,
        })

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

@router.get("/{jogador_id}/estatisticas/casa-fora", response_model=EstatisticasCasaForaResponse)
def estatisticas_casa_fora(jogador_id: int, temporada: int = Query(2023), local: str = Query(..., description="casa ou fora"), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
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
        return {
            "jogador_id": jogador_id, 
            "nome_jogador": f"{jogador.firstname} {jogador.lastname}", 
            "temporada": temporada, 
            "local": local, 
            "mensagem": f"Sem dados para jogos {local}."
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

        lista_jogos.append({
            "jogo_id": jogo.id,
            "data": jogo.date_start,
            "pontos": stat.points,
            "assistencias": stat.assists,
            "rebotes": stat.tot_reb,
            "roubos": stat.steals,
            "bloqueios": stat.blocks,
            "turnovers": stat.turnovers,
        })

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