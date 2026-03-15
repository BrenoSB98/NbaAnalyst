import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from app.db.db_utils import get_db
from app.db.models import Game, GameTeamScore, League, Player, PlayerTeamSeason, Team, TeamLeagueInfo
from app.routers.auth import obter_usuario_atual
from app.schemas.player import ElencoTimeResponse
from app.schemas.team import ComparacaoTimesResponse, EstatisticasTimeResponse, PerformanceTimeResponse, TeamDetalheResponse, TeamListResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=TeamListResponse)
def listar_times(page: int = Query(1, ge=1), page_size: int = Query(30, ge=1, le=100), nba_franchise: bool = Query(None), cidade: str = Query(None), nome: str = Query(None), db: Session = Depends(get_db)):
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

@router.get("/comparar", response_model=ComparacaoTimesResponse)
def comparar_times(time1_id: int = Query(...), time2_id: int = Query(...), temporada: int = Query(2023), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
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

    confrontos = (db.query(Game).filter(Game.season == temporada, or_(and_(Game.home_team_id == time1_id, Game.away_team_id == time2_id),
                                        and_(Game.home_team_id == time2_id, Game.away_team_id == time1_id)), Game.status_short == 3).all())

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

@router.get("/{time_id}", response_model=TeamDetalheResponse)
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

@router.get("/{time_id}/elenco", response_model=ElencoTimeResponse)
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

@router.get("/{time_id}/estatisticas", response_model=EstatisticasTimeResponse)
def estatisticas_time(time_id: int, temporada: int = Query(2023), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
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

@router.get("/{time_id}/performance", response_model=PerformanceTimeResponse)
def performance_time(time_id: int, temporada: int = Query(2023), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    time = db.query(Team).filter(Team.id == time_id).first()
    if not time:
        logger.warning(f"Time não encontrado ao buscar performance: id={time_id}")
        raise HTTPException(status_code=404, detail="Time não encontrado.")

    jogos = (db.query(Game, GameTeamScore).join(GameTeamScore, GameTeamScore.game_id == Game.id)
             .filter(Game.season == temporada, GameTeamScore.team_id == time_id, Game.status_short == 3)
             .order_by(Game.date_start.desc()).all())

    if len(jogos) == 0:
        return {
            "time_id": time_id, 
            "nome_time": time.name, 
            "temporada": temporada,
            "total_jogos": 0, 
            "vitorias": 0, 
            "derrotas": 0, 
            "aproveitamento": 0.0,
            "record_casa": "0-0", 
            "record_fora": "0-0",
            "media_pontos_feitos": 0.0, 
            "media_pontos_sofridos": 0.0, 
            "diferencial_pontos": 0.0,
            "ultimos_5_jogos": [], 
            "mensagem": "Sem jogos finalizados nesta temporada."
        }

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

        if score.points is not None:
            pontos_feitos = score.points     
        else:
            pontos_feitos = 0
        if adversario.points is not None:
            pontos_sofridos = adversario.points    
        else:
            pontos_sofridos = 0

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
            if em_casa:
                adversario_id = jogo.away_team_id 
            else:
                adversario_id = jogo.home_team_id
            if vitoria:
                resultado = "V" 
            else:
                resultado = "D"
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
    media_pontos_feitos = 0.0
    media_pontos_sofridos = 0.0
    diferencial = 0.0
    aproveitamento = 0.0

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