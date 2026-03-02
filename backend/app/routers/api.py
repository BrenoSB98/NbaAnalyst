import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, desc

from app.db.db_utils import get_db
from app.db.models import Team, Game, GameTeamScore, GameTeamStats, Player, PlayerTeamSeason, PlayerGameStats, Season, League, TeamLeagueInfo, TeamSeasonStats
from app.routers import analytics, predictions, bet, onerb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
router.include_router(predictions.router, prefix="/predictions", tags=["Predictions"])
router.include_router(bet.router, prefix="/bet", tags=["Betting"])
router.include_router(onerb.router, prefix="/onerb", tags=["Onerb"])

@router.get("/teams")
def listar_times(page: int = Query(1, ge=1), page_size: int = Query(30, ge=1, le=100), nba_franchise: bool = Query(None), city: str = Query(None), name: str = Query(None), db: Session = Depends(get_db),):
    try:
        query = db.query(Team)
        if nba_franchise is not None:
            query = query.filter(Team.nba_franchise == nba_franchise)
        if city:
            query = query.filter(Team.city.ilike(f"%{city}%"))
        if name:
            query = query.filter(Team.name.ilike(f"%{name}%"))

        total = query.count()
        offset = (page - 1) * page_size
        times = query.order_by(Team.name.asc()).offset(offset).limit(page_size).all()

        lista_times = []
        for time in times:
            time_dict = {"id": time.id, "name": time.name, "nickname": time.nickname, "code": time.code, 
                         "city": time.city, "logo": time.logo, "nba_franchise": time.nba_franchise, "all_star": time.all_star
                        }
            lista_times.append(time_dict)
        resposta = {"total": total, "page": page, "page_size": page_size, "teams": lista_times}
        return resposta

    except Exception as e:
        logger.error(f"Não foi possível listar os times: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/teams/{team_id}")
def obter_time(team_id: int, db: Session = Depends(get_db)):
    try:
        time = db.query(Team).filter(Team.id == team_id).first()

        if not time:
            raise HTTPException(status_code=404, detail="Time não encontrado")

        league_info_query = (db.query(TeamLeagueInfo, League).join(League, TeamLeagueInfo.league_id == League.id).filter(TeamLeagueInfo.team_id == team_id).first())

        resultado = {"id": time.id, "name": time.name, "nickname": time.nickname, "code": time.code, "city": time.city,
                     "logo": time.logo, "all_star": time.all_star, "nba_franchise": time.nba_franchise, "league_info": None
                    }

        if league_info_query:
            team_league_info = league_info_query[0]
            league = league_info_query[1]
            resultado["league_info"] = {"league_name": league.code, "conference": team_league_info.conference, "division": team_league_info.division}
        return resultado

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Não foi possível obter informações do time: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/teams/{team_id}/roster")
def obter_elenco(team_id: int, season: int = Query(2023), db: Session = Depends(get_db)):
    try:
        time = db.query(Team).filter(Team.id == team_id).first()
        if not time:
            raise HTTPException(status_code=404, detail="Time não encontrado")

        jogadores_query = (db.query(Player, PlayerTeamSeason).join(PlayerTeamSeason, PlayerTeamSeason.player_id == Player.id)
                           .filter(PlayerTeamSeason.team_id == team_id, PlayerTeamSeason.season == season).all()
                           )

        lista_jogadores = []
        for jogador_data in jogadores_query:
            jogador = jogador_data[0]
            jogador_time_season = jogador_data[1]
            altura_metros = None
            if jogador.height_meters is not None:
                altura_metros = float(jogador.height_meters)

            peso_kg = None
            if jogador.weight_kilograms is not None:
                peso_kg = float(jogador.weight_kilograms)

            jogador_dict = {"id": jogador.id, "firstname": jogador.firstname, "lastname": jogador.lastname,
                            "jersey": jogador_time_season.jersey, "position": jogador_time_season.pos,
                            "active": jogador_time_season.active, "height_meters": altura_metros, "weight_kilograms": peso_kg
                            }
            lista_jogadores.append(jogador_dict)
        resposta = {"team_id": team_id, "team_name": time.name, "season": season, "count": len(lista_jogadores), "players": lista_jogadores}
        return resposta

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Não foi possível obter o elenco do time: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/teams/{team_id}/stats")
def stats_time(team_id: int, season: int = Query(2023), db: Session = Depends(get_db)):
    try:
        time = db.query(Team).filter(Team.id == team_id).first()
        if not time:
            raise HTTPException(status_code=404, detail="Time não encontrado")

        query_jogos = db.query(Game).filter(or_(Game.home_team_id == team_id, Game.away_team_id == team_id), Game.season == season)
        total_jogos = query_jogos.count()

        jogos_casa = query_jogos.filter(Game.home_team_id == team_id).count()
        jogos_fora = query_jogos.filter(Game.away_team_id == team_id).count()
        total_jogadores = (db.query(PlayerTeamSeason).filter(PlayerTeamSeason.team_id == team_id, PlayerTeamSeason.season == season).count())
        jogos_finalizados = (db.query(Game, GameTeamScore).join(GameTeamScore, GameTeamScore.game_id == Game.id).filter(
            Game.season == season, GameTeamScore.team_id == team_id, Game.status_short == 3).all()
                             )

        vitorias = 0
        derrotas = 0

        for jogo_data in jogos_finalizados:
            jogo = jogo_data[0]
            score_time = jogo_data[1]
            score_adversario = (db.query(GameTeamScore).filter(GameTeamScore.game_id == jogo.id, GameTeamScore.team_id != team_id).first())

            if score_adversario:
                pontos_time = score_time.points
                pontos_adversario = score_adversario.points

                if pontos_time > pontos_adversario:
                    vitorias = vitorias + 1
                else:
                    derrotas = derrotas + 1

        total_jogos_finalizados = vitorias + derrotas
        win_rate = 0
        if total_jogos_finalizados > 0:
            win_rate = round(vitorias / total_jogos_finalizados * 100, 2)

        resposta = {"team_id": team_id, "team_name": time.name, "season": season, "total_games": total_jogos,
                    "home_games": jogos_casa, "away_games": jogos_fora, "total_players": total_jogadores, "wins": vitorias,
                    "losses": derrotas, "win_rate": win_rate
                    }
        return resposta

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Não foi possível obter as estatísticas do time: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/teams/{team_id}/performance")
def performance_time(team_id: int, season: int = Query(2023), db: Session = Depends(get_db)):
    try:
        time = db.query(Team).filter(Team.id == team_id).first()
        if not time:
            raise HTTPException(status_code=404, detail="Time não encontrado")

        jogos = (db.query(Game, GameTeamScore).join(GameTeamScore, GameTeamScore.game_id == Game.id).filter(Game.season == season,
                                                                                                            GameTeamScore.team_id == team_id,
                                                                                                            Game.status_short == 3)
                 .order_by(Game.date_start.desc()).all()
                 )

        if len(jogos) == 0:
            resposta = {"team_id": team_id, "team_name": time.name, "season": season, "message": "Sem jogos finalizados nesta temporada"}
            return resposta

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

            adversario_score = (db.query(GameTeamScore).filter(GameTeamScore.game_id == jogo.id, GameTeamScore.team_id != team_id).first())

            if not adversario_score:
                continue

            pontos_feitos = score.points
            if pontos_feitos is None:
                pontos_feitos = 0

            pontos_sofridos = adversario_score.points
            if pontos_sofridos is None:
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
                    resultado = "W"
                else:
                    resultado = "L"

                jogo_dict = {"game_id": jogo.id, "date": jogo.date_start, "opponent_id": adversario_id, "home": em_casa, 
                             "points_scored": pontos_feitos, "points_allowed": pontos_sofridos, "result": resultado
                             }
                ultimos_5.append(jogo_dict)
            contador = contador + 1

        total_jogos = len(jogos)
        total_vitorias = vitorias_casa + vitorias_fora
        total_derrotas = derrotas_casa + derrotas_fora

        media_pontos_feitos = 0
        media_pontos_sofridos = 0
        diferencial_pontos = 0
        win_rate = 0

        if total_jogos > 0:
            media_pontos_feitos = round(total_pontos_feitos / total_jogos, 2)
            media_pontos_sofridos = round(total_pontos_sofridos / total_jogos, 2)
            diferencial_pontos = round((total_pontos_feitos - total_pontos_sofridos) / total_jogos, 2)
            win_rate = round(total_vitorias / total_jogos * 100, 2)

        resposta = {
            "team_id": team_id,
            "team_name": time.name,
            "season": season,
            "total_games": total_jogos,
            "wins": total_vitorias,
            "losses": total_derrotas,
            "win_rate": win_rate,
            "home_record": f"{vitorias_casa}-{derrotas_casa}",
            "away_record": f"{vitorias_fora}-{derrotas_fora}",
            "avg_points_scored": media_pontos_feitos,
            "avg_points_allowed": media_pontos_sofridos,
            "point_differential": diferencial_pontos,
            "last_5_games": ultimos_5
        }
        return resposta

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Não foi possível calcular a performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/teams/compare")
def comparar_times(team1_id: int = Query(...), team2_id: int = Query(...), season: int = Query(2023), db: Session = Depends(get_db)):
    try:
        time1 = db.query(Team).filter(Team.id == team1_id).first()
        time2 = db.query(Team).filter(Team.id == team2_id).first()

        if not time1 or not time2:
            raise HTTPException(status_code=404, detail="Um ou ambos os times não foram encontrados")

        jogos_time1 = (db.query(Game, GameTeamScore).join(GameTeamScore, GameTeamScore.game_id == Game.id)
                       .filter(Game.season == season, GameTeamScore.team_id == team1_id, Game.status_short == 3).all()
                       )

        vitorias_time1 = 0
        derrotas_time1 = 0

        for jogo_data in jogos_time1:
            jogo = jogo_data[0]
            score = jogo_data[1]

            adversario_score = (db.query(GameTeamScore).filter(GameTeamScore.game_id == jogo.id, GameTeamScore.team_id != team1_id).first())

            if adversario_score:
                if score.points > adversario_score.points:
                    vitorias_time1 = vitorias_time1 + 1
                else:
                    derrotas_time1 = derrotas_time1 + 1

        jogos_time2 = (db.query(Game, GameTeamScore).join(GameTeamScore, GameTeamScore.game_id == Game.id)
                       .filter(Game.season == season, GameTeamScore.team_id == team2_id, Game.status_short == 3).all()
                       )

        vitorias_time2 = 0
        derrotas_time2 = 0

        for jogo_data in jogos_time2:
            jogo = jogo_data[0]
            score = jogo_data[1]

            adversario_score = (db.query(GameTeamScore).filter(GameTeamScore.game_id == jogo.id, GameTeamScore.team_id != team2_id).first())

            if adversario_score:
                if score.points > adversario_score.points:
                    vitorias_time2 = vitorias_time2 + 1
                else:
                    derrotas_time2 = derrotas_time2 + 1

        total_jogos_time1 = vitorias_time1 + derrotas_time1
        win_rate_time1 = 0
        if total_jogos_time1 > 0:
            win_rate_time1 = round(vitorias_time1 / total_jogos_time1 * 100, 2)

        total_jogos_time2 = vitorias_time2 + derrotas_time2
        win_rate_time2 = 0
        if total_jogos_time2 > 0:
            win_rate_time2 = round(vitorias_time2 / total_jogos_time2 * 100, 2)

        confrontos = (db.query(Game).filter(Game.season == season,or_(and_(Game.home_team_id == team1_id, Game.away_team_id == team2_id),
                                                                      and_(Game.home_team_id == team2_id, Game.away_team_id == team1_id)),
                                            Game.status_short == 3).all()
                      )

        vitorias_time1_h2h = 0
        vitorias_time2_h2h = 0

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
                if jogo.home_team_id == team1_id:
                    if home_points > away_points:
                        vitorias_time1_h2h = vitorias_time1_h2h + 1
                    else:
                        vitorias_time2_h2h = vitorias_time2_h2h + 1
                else:
                    if away_points > home_points:
                        vitorias_time1_h2h = vitorias_time1_h2h + 1
                    else:
                        vitorias_time2_h2h = vitorias_time2_h2h + 1

        resposta = {
            "season": season,
            "team1": {
                "id": time1.id,
                "name": time1.name,
                "wins": vitorias_time1,
                "losses": derrotas_time1,
                "win_rate": win_rate_time1
            },
            "team2": {
                "id": time2.id,
                "name": time2.name,
                "wins": vitorias_time2,
                "losses": derrotas_time2,
                "win_rate": win_rate_time2
            },
            "head_to_head": {
                "total_games": len(confrontos),
                "team1_wins": vitorias_time1_h2h,
                "team2_wins": vitorias_time2_h2h
            }
        }
        return resposta

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao comparar times: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/games")
def listar_jogos(season: int = Query(None), team_id: int = Query(None), date_from: str = Query(None), date_to: str = Query(None),
                 status: int = Query(None), page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    try:
        query = db.query(Game)

        if season is not None:
            query = query.filter(Game.season == season)
        if team_id is not None:
            query = query.filter(or_(Game.home_team_id == team_id, Game.away_team_id == team_id))
        if date_from:
            query = query.filter(Game.date_start >= date_from)
        if date_to:
            query = query.filter(Game.date_start <= date_to)
        if status is not None:
            query = query.filter(Game.status_short == status)

        total = query.count()
        offset = (page - 1) * page_size
        jogos = query.order_by(Game.date_start.desc()).offset(offset).limit(page_size).all()
        lista_jogos = []
        
        for jogo in jogos:
            scores = db.query(GameTeamScore).filter(GameTeamScore.game_id == jogo.id).all()

            home_points = None
            away_points = None

            for score in scores:
                if score.is_home:
                    home_points = score.points
                else:
                    away_points = score.points

            jogo_dict = {"id": jogo.id, "season": jogo.season, "league": jogo.league, "date_start": jogo.date_start,
                         "status_short": jogo.status_short, "status_long": jogo.status_long, "home_team_id": jogo.home_team_id,
                         "away_team_id": jogo.away_team_id, "home_points": home_points, "away_points": away_points,
                         "arena_name": jogo.arena_name, "arena_city": jogo.arena_city
                         }
            lista_jogos.append(jogo_dict)

        resposta = {"total": total, "page": page, "page_size": page_size, "count": len(lista_jogos), "games": lista_jogos}
        return resposta

    except Exception as e:
        logger.error(f"Não foi possível listar os jogos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/games/{game_id}")
def obter_jogo(game_id: int, db: Session = Depends(get_db)):
    try:
        jogo = db.query(Game).filter(Game.id == game_id).first()
        if not jogo:
            raise HTTPException(status_code=404, detail="Jogo não encontrado")

        scores = db.query(GameTeamScore).filter(GameTeamScore.game_id == game_id).all()

        home_points = None
        away_points = None
        home_score_detail = None
        away_score_detail = None

        for score in scores:
            if score.is_home:
                home_points = score.points
                home_score_detail = score
            else:
                away_points = score.points
                away_score_detail = score

        home_team = db.query(Team).filter(Team.id == jogo.home_team_id).first()
        away_team = db.query(Team).filter(Team.id == jogo.away_team_id).first()

        home_team_info = {"id": jogo.home_team_id, "name": None, "nickname": None, "logo": None, "points": home_points, "linescore": None}

        if home_team:
            home_team_info["name"] = home_team.name
            home_team_info["nickname"] = home_team.nickname
            home_team_info["logo"] = home_team.logo

        if home_score_detail:
            home_team_info["linescore"] = {"q1": home_score_detail.linescore_q1, "q2": home_score_detail.linescore_q2,
                                           "q3": home_score_detail.linescore_q3, "q4": home_score_detail.linescore_q4
                                           }
        away_team_info = {"id": jogo.away_team_id, "name": None, "nickname": None, "logo": None, "points": away_points, "linescore": None}

        if away_team:
            away_team_info["name"] = away_team.name
            away_team_info["nickname"] = away_team.nickname
            away_team_info["logo"] = away_team.logo

        if away_score_detail:
            away_team_info["linescore"] = {"q1": away_score_detail.linescore_q1, "q2": away_score_detail.linescore_q2,
                                           "q3": away_score_detail.linescore_q3, "q4": away_score_detail.linescore_q4
                                           }
        resposta = {
            "id": jogo.id,
            "season": jogo.season,
            "league": jogo.league,
            "date_start": jogo.date_start,
            "date_end": jogo.date_end,
            "duration": jogo.duration,
            "status_short": jogo.status_short,
            "status_long": jogo.status_long,
            "stage": jogo.stage,
            "periods_current": jogo.periods_current,
            "periods_total": jogo.periods_total,
            "arena": {
                "name": jogo.arena_name,
                "city": jogo.arena_city,
                "state": jogo.arena_state,
                "country": jogo.arena_country
            },
            "home_team": home_team_info,
            "away_team": away_team_info,
            "times_tied": jogo.times_tied,
            "lead_changes": jogo.lead_changes,
            "nugget": jogo.nugget
        }
        return resposta

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Não foi possível obter informações do jogo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/games/{game_id}/team-stats")
def stats_times_jogo(game_id: int, db: Session = Depends(get_db)):
    try:
        jogo = db.query(Game).filter(Game.id == game_id).first()
        if not jogo:
            raise HTTPException(status_code=404, detail="Jogo não encontrado")

        stats = db.query(GameTeamStats).filter(GameTeamStats.game_id == game_id).all()

        lista_stats = []
        for stat in stats:
            team = db.query(Team).filter(Team.id == stat.team_id).first()
            team_name = None
            if team:
                team_name = team.name

            fgp_value = None
            if stat.fgp is not None:
                fgp_value = float(stat.fgp)

            ftp_value = None
            if stat.ftp is not None:
                ftp_value = float(stat.ftp)

            tpp_value = None
            if stat.tpp is not None:
                tpp_value = float(stat.tpp)

            stat_dict = {
                "team_id": stat.team_id,
                "team_name": team_name,
                "points": stat.points,
                "fgm": stat.fgm,
                "fga": stat.fga,
                "fgp": fgp_value,
                "ftm": stat.ftm,
                "fta": stat.fta,
                "ftp": ftp_value,
                "tpm": stat.tpm,
                "tpa": stat.tpa,
                "tpp": tpp_value,
                "off_reb": stat.off_reb,
                "def_reb": stat.def_reb,
                "tot_reb": stat.tot_reb,
                "assists": stat.assists,
                "steals": stat.steals,
                "blocks": stat.blocks,
                "turnovers": stat.turnovers,
                "p_fouls": stat.p_fouls,
                "plus_minus": stat.plus_minus,
                "fast_break_points": stat.fast_break_points,
                "points_in_paint": stat.points_in_paint,
                "second_chance_points": stat.second_chance_points,
                "points_off_turnovers": stat.points_off_turnovers,
                "biggest_lead": stat.biggest_lead,
                "longest_run": stat.longest_run
            }
            lista_stats.append(stat_dict)

        resposta = {"game_id": game_id, "teams_stats": lista_stats}
        return resposta

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Não foi possível obter estatísticas dos times do jogo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/games/upcoming")
def proximos_jogos(days: int = Query(7, ge=1, le=30), team_id: int = Query(None), db: Session = Depends(get_db)):
    try:
        hoje = datetime.now()
        data_limite = hoje + timedelta(days=days)
        query = db.query(Game).filter(Game.date_start >= hoje, Game.date_start <= data_limite, Game.status_short == 1)

        if team_id:
            query = query.filter(or_(Game.home_team_id == team_id, Game.away_team_id == team_id))

        jogos = query.order_by(Game.date_start.asc()).all()

        lista_jogos = []
        for jogo in jogos:
            home_team = db.query(Team).filter(Team.id == jogo.home_team_id).first()
            away_team = db.query(Team).filter(Team.id == jogo.away_team_id).first()

            home_team_name = None
            if home_team:
                home_team_name = home_team.name

            away_team_name = None
            if away_team:
                away_team_name = away_team.name

            jogo_dict = {
                "id": jogo.id,
                "date_start": jogo.date_start,
                "home_team": {"id": jogo.home_team_id, "name": home_team_name},
                "away_team": {"id": jogo.away_team_id, "name": away_team_name},
                "arena_name": jogo.arena_name
                }
            lista_jogos.append(jogo_dict)
            
        resposta = {"count": len(lista_jogos), "days": days, "games": lista_jogos}
        return resposta

    except Exception as e:
        logger.error(f"Não foi possível obter próximos jogos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/players")
def listar_jogadores(team_id: int = Query(None), season: int = Query(None), firstname: str = Query(None), lastname: str = Query(None),
                     page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    try:
        query = db.query(Player)

        if team_id is not None or season is not None:
            query = query.join(PlayerTeamSeason, PlayerTeamSeason.player_id == Player.id)
            if team_id is not None:
                query = query.filter(PlayerTeamSeason.team_id == team_id)
            if season is not None:
                query = query.filter(PlayerTeamSeason.season == season)
            query = query.distinct()

        if firstname:
            query = query.filter(Player.firstname.ilike(f"%{firstname}%"))
        if lastname:
            query = query.filter(Player.lastname.ilike(f"%{lastname}%"))

        total = query.count()
        offset = (page - 1) * page_size
        jogadores = query.order_by(Player.lastname.asc()).offset(offset).limit(page_size).all()
        
        lista_jogadores = []
        for jogador in jogadores:
            altura_metros = None
            if jogador.height_meters is not None:
                altura_metros = float(jogador.height_meters)

            peso_kg = None
            if jogador.weight_kilograms is not None:
                peso_kg = float(jogador.weight_kilograms)

            jogador_dict = {
                "id": jogador.id,
                "firstname": jogador.firstname,
                "lastname": jogador.lastname,
                "birth_date": jogador.birth_date,
                "birth_country": jogador.birth_country,
                "nba_start": jogador.nba_start,
                "nba_pro": jogador.nba_pro,
                "height_feet": jogador.height_feet,
                "height_inches": jogador.height_inches,
                "height_meters": altura_metros,
                "weight_pounds": jogador.weight_pounds,
                "weight_kilograms": peso_kg,
                "college": jogador.college,
                "affiliation": jogador.affiliation,
            }
            lista_jogadores.append(jogador_dict)

        resposta = {"total": total, "page": page, "page_size": page_size, "count": len(lista_jogadores), "players": lista_jogadores}
        return resposta

    except Exception as e:
        logger.error(f"Não foi possível listar jogadores: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/players/{player_id}")
def obter_jogador(player_id: int, db: Session = Depends(get_db)):
    try:
        jogador = db.query(Player).filter(Player.id == player_id).first()
        if not jogador:
            raise HTTPException(status_code=404, detail="Jogador não encontrado")

        times_jogador = (db.query(PlayerTeamSeason, Team).join(Team, PlayerTeamSeason.team_id == Team.id)
                         .filter(PlayerTeamSeason.player_id == player_id).order_by(PlayerTeamSeason.season.desc()).all()
                         )

        lista_times = []
        for time_data in times_jogador:
            pts = time_data[0]
            team = time_data[1]

            time_dict = {"season": pts.season, "team_id": pts.team_id, "team_name": team.name, "jersey": pts.jersey, "position": pts.pos, "active": pts.active}
            lista_times.append(time_dict)

        altura_metros = None
        if jogador.height_meters is not None:
            altura_metros = float(jogador.height_meters)

        peso_kg = None
        if jogador.weight_kilograms is not None:
            peso_kg = float(jogador.weight_kilograms)

        resposta = {
            "id": jogador.id,
            "firstname": jogador.firstname,
            "lastname": jogador.lastname,
            "birth_date": jogador.birth_date,
            "birth_country": jogador.birth_country,
            "nba_start": jogador.nba_start,
            "nba_pro": jogador.nba_pro,
            "height_feet": jogador.height_feet,
            "height_inches": jogador.height_inches,
            "height_meters": altura_metros,
            "weight_pounds": jogador.weight_pounds,
            "weight_kilograms": peso_kg,
            "college": jogador.college,
            "affiliation": jogador.affiliation,
            "teams_history": lista_times
        }
        return resposta

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Não foi possível obter detalhes do jogador: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/players/{player_id}/stats/season")
def stats_temporada_jogador(player_id: int, season: int = Query(2023), db: Session = Depends(get_db)):
    try:
        jogador = db.query(Player).filter(Player.id == player_id).first()
        if not jogador:
            raise HTTPException(status_code=404, detail="Jogador não encontrado")

        stats = (db.query(PlayerGameStats).join(Game, PlayerGameStats.game_id == Game.id).filter(PlayerGameStats.player_id == player_id,
                                                                                                 Game.season == season, Game.status_short == 3).all()
                 )

        if len(stats) == 0:
            resposta = {"player_id": player_id, "player_name": f"{jogador.firstname} {jogador.lastname}", "season": season, "message": "Sem dados para esta temporada"}
            return resposta

        total_points = 0
        total_assists = 0
        total_rebounds = 0
        total_steals = 0
        total_blocks = 0
        total_turnovers = 0

        for stat in stats:
            if stat.points:
                total_points = total_points + stat.points
            if stat.assists:
                total_assists = total_assists + stat.assists
            if stat.tot_reb:
                total_rebounds = total_rebounds + stat.tot_reb
            if stat.steals:
                total_steals = total_steals + stat.steals
            if stat.blocks:
                total_blocks = total_blocks + stat.blocks
            if stat.turnovers:
                total_turnovers = total_turnovers + stat.turnovers

        fgp_values = []
        tpp_values = []
        ftp_values = []

        for stat in stats:
            if stat.fgp is not None:
                fgp_values.append(float(stat.fgp))
            if stat.tpp is not None:
                tpp_values.append(float(stat.tpp))
            if stat.ftp is not None:
                ftp_values.append(float(stat.ftp))

        num_jogos = len(stats)

        media_points = round(total_points / num_jogos, 2)
        media_assists = round(total_assists / num_jogos, 2)
        media_rebounds = round(total_rebounds / num_jogos, 2)
        media_steals = round(total_steals / num_jogos, 2)
        media_blocks = round(total_blocks / num_jogos, 2)
        media_turnovers = round(total_turnovers / num_jogos, 2)

        media_fg_pct = 0
        if len(fgp_values) > 0:
            soma_fgp = sum(fgp_values)
            media_fg_pct = round(soma_fgp / len(fgp_values), 2)

        media_three_pct = 0
        if len(tpp_values) > 0:
            soma_tpp = sum(tpp_values)
            media_three_pct = round(soma_tpp / len(tpp_values), 2)

        media_ft_pct = 0
        if len(ftp_values) > 0:
            soma_ftp = sum(ftp_values)
            media_ft_pct = round(soma_ftp / len(ftp_values), 2)

        resposta = {"player_id": player_id, "player_name": f"{jogador.firstname} {jogador.lastname}", "season": season, "games_played": num_jogos,
                    "totals": {
                        "points": total_points,
                        "assists": total_assists,
                        "rebounds": total_rebounds,
                        "steals": total_steals,
                        "blocks": total_blocks,
                        "turnovers": total_turnovers
                        },
                    "averages": {
                        "points": media_points,
                        "assists": media_assists,
                        "rebounds": media_rebounds,
                        "steals": media_steals,
                        "blocks": media_blocks,
                        "turnovers": media_turnovers,
                        "fg_pct": media_fg_pct,
                        "three_pct": media_three_pct,
                        "ft_pct": media_ft_pct
                        }
                    }
        return resposta

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Não foi possível calcular estatísticas de temporada: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/players/{player_id}/stats/games")
def stats_jogos_jogador(player_id: int, season: int = Query(None), limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    try:
        jogador = db.query(Player).filter(Player.id == player_id).first()
        if not jogador:
            raise HTTPException(status_code=404, detail="Jogador não encontrado")

        query = (db.query(PlayerGameStats, Game).join(Game, PlayerGameStats.game_id == Game.id).filter(PlayerGameStats.player_id == player_id))

        if season:
            query = query.filter(Game.season == season)
        stats = query.order_by(Game.date_start.desc()).limit(limit).all()

        lista_jogos = []
        for stat_data in stats:
            stat = stat_data[0]
            jogo = stat_data[1]

            if stat.team_id == jogo.home_team_id:
                adversario_id = jogo.away_team_id
            else:
                adversario_id = jogo.home_team_id

            fgp_value = None
            if stat.fgp is not None:
                fgp_value = float(stat.fgp)

            tpp_value = None
            if stat.tpp is not None:
                tpp_value = float(stat.tpp)

            ftp_value = None
            if stat.ftp is not None:
                ftp_value = float(stat.ftp)

            jogo_dict = {"game_id": stat.game_id, "date": jogo.date_start, "season": jogo.season, "opponent_id": adversario_id, "minutes": stat.minutes,
                         "points": stat.points, "assists": stat.assists, "rebounds": stat.tot_reb, "steals": stat.steals, "blocks": stat.blocks,
                         "turnovers": stat.turnovers, "fg_pct": fgp_value, "three_pct": tpp_value, "ft_pct": ftp_value, "plus_minus": stat.plus_minus
                         }
            lista_jogos.append(jogo_dict)
            
        resposta = {"player_id": player_id, "player_name": f"{jogador.firstname} {jogador.lastname}", "count": len(lista_jogos), "games": lista_jogos}
        return resposta

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Não foi possível calcular estatísticas de jogos do jogador: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/game/{game_id}")
def stats_por_jogo(game_id: int, db: Session = Depends(get_db)):
    try:
        jogo = db.query(Game).filter(Game.id == game_id).first()
        if not jogo:
            raise HTTPException(status_code=404, detail="Jogo não encontrado")

        stats = (db.query(PlayerGameStats, Player).join(Player, PlayerGameStats.player_id == Player.id).filter(PlayerGameStats.game_id == game_id).all())

        lista_stats = []
        for stat_data in stats:
            stat = stat_data[0]
            player = stat_data[1]

            fgp_value = None
            if stat.fgp is not None:
                fgp_value = float(stat.fgp)

            ftp_value = None
            if stat.ftp is not None:
                ftp_value = float(stat.ftp)

            tpp_value = None
            if stat.tpp is not None:
                tpp_value = float(stat.tpp)

            stat_dict = {
                "player_id": stat.player_id,
                "player_name": f"{player.firstname} {player.lastname}",
                "team_id": stat.team_id,
                "position": stat.pos,
                "minutes": stat.minutes,
                "points": stat.points,
                "assists": stat.assists,
                "tot_reb": stat.tot_reb,
                "off_reb": stat.off_reb,
                "def_reb": stat.def_reb,
                "steals": stat.steals,
                "blocks": stat.blocks,
                "turnovers": stat.turnovers,
                "p_fouls": stat.p_fouls,
                "fgm": stat.fgm,
                "fga": stat.fga,
                "fgp": fgp_value,
                "ftm": stat.ftm,
                "fta": stat.fta,
                "ftp": ftp_value,
                "tpm": stat.tpm,
                "tpa": stat.tpa,
                "tpp": tpp_value,
                "plus_minus": stat.plus_minus,
                "comment": stat.comment,
            }
            lista_stats.append(stat_dict)

        resposta = {"game_id": game_id, "count": len(lista_stats), "stats": lista_stats}
        return resposta

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Não foi possível calcular estatísticas do jogo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/players/{player_id}/stats/last-n-games")
def stats_ultimos_n_jogos(player_id: int, n_games: int = Query(10, description="5, 10, 15 ou 20 jogos"), 
                          season: int = Query(None), db: Session = Depends(get_db)):
    try:
        jogador = db.query(Player).filter(Player.id == player_id).first()
        if not jogador:
            raise HTTPException(status_code=404, detail="Jogador não encontrado")

        valores_permitidos = [5, 10, 15, 20]
        if n_games not in valores_permitidos:
            raise HTTPException(status_code=400, detail=f"n_games deve ser um dos valores: {valores_permitidos}")

        query = (db.query(PlayerGameStats, Game).join(Game, PlayerGameStats.game_id == Game.id).filter(PlayerGameStats.player_id == player_id, Game.status_short == 3))

        if season:
            query = query.filter(Game.season == season)
        stats = query.order_by(Game.date_start.desc()).limit(n_games).all()

        if len(stats) == 0:
            resposta = {"player_id": player_id, "player_name": f"{jogador.firstname} {jogador.lastname}", "n_games": n_games,
                        "season": season, "message": "Sem dados para calcular"
                        }
            return resposta

        total_points = 0
        total_assists = 0
        total_rebounds = 0
        total_steals = 0
        total_blocks = 0
        total_turnovers = 0
        total_minutes = 0
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

            if stat.points:
                valor = stat.points
                if isinstance(valor, str):
                    valor = int(valor)
                total_points = total_points + valor
                
            if stat.assists:
                valor = stat.assists
                if isinstance(valor, str):
                    valor = int(valor)
                total_assists = total_assists + valor
                
            if stat.tot_reb:
                valor = stat.tot_reb
                if isinstance(valor, str):
                    valor = int(valor)
                total_rebounds = total_rebounds + valor
                
            if stat.steals:
                valor = stat.steals
                if isinstance(valor, str):
                    valor = int(valor)
                total_steals = total_steals + valor
                
            if stat.blocks:
                valor = stat.blocks
                if isinstance(valor, str):
                    valor = int(valor)
                total_blocks = total_blocks + valor
                
            if stat.turnovers:
                valor = stat.turnovers
                if isinstance(valor, str):
                    valor = int(valor)
                total_turnovers = total_turnovers + valor
                
            if stat.minutes:
                valor = stat.minutes
                if isinstance(valor, str):
                    valor = int(valor)
                total_minutes = total_minutes + valor
                
            if stat.fgm:
                valor = stat.fgm
                if isinstance(valor, str):
                    valor = int(valor)
                total_fgm = total_fgm + valor
                
            if stat.fga:
                valor = stat.fga
                if isinstance(valor, str):
                    valor = int(valor)
                total_fga = total_fga + valor
                
            if stat.tpm:
                valor = stat.tpm
                if isinstance(valor, str):
                    valor = int(valor)
                total_tpm = total_tpm + valor
                
            if stat.tpa:
                valor = stat.tpa
                if isinstance(valor, str):
                    valor = int(valor)
                total_tpa = total_tpa + valor
                
            if stat.ftm:
                valor = stat.ftm
                if isinstance(valor, str):
                    valor = int(valor)
                total_ftm = total_ftm + valor
                
            if stat.fta:
                valor = stat.fta
                if isinstance(valor, str):
                    valor = int(valor)
                total_fta = total_fta + valor

            jogo_info = {"game_id": jogo.id, "date": jogo.date_start, "points": stat.points, "assists": stat.assists, "rebounds": stat.tot_reb}
            lista_jogos.append(jogo_info)

        num_jogos = len(stats)

        media_points = round(total_points / num_jogos, 2)
        media_assists = round(total_assists / num_jogos, 2)
        media_rebounds = round(total_rebounds / num_jogos, 2)
        media_steals = round(total_steals / num_jogos, 2)
        media_blocks = round(total_blocks / num_jogos, 2)
        media_turnovers = round(total_turnovers / num_jogos, 2)
        media_minutes = round(total_minutes / num_jogos, 2)

        fg_pct = 0
        if total_fga > 0:
            fg_pct = round((total_fgm / total_fga) * 100, 2)
        three_pct = 0
        if total_tpa > 0:
            three_pct = round((total_tpm / total_tpa) * 100, 2)
        ft_pct = 0
        if total_fta > 0:
            ft_pct = round((total_ftm / total_fta) * 100, 2)

        resposta = {"player_id": player_id, "player_name": f"{jogador.firstname} {jogador.lastname}", "n_games": n_games,
                    "games_analyzed": num_jogos, "season": season,
                    "averages": {
                        "points": media_points,
                        "assists": media_assists,
                        "rebounds": media_rebounds,
                        "steals": media_steals,
                        "blocks": media_blocks,
                        "turnovers": media_turnovers,
                        "minutes": media_minutes,
                        "fg_pct": fg_pct,
                        "three_pct": three_pct,
                        "ft_pct": ft_pct
                        },
                    "games": lista_jogos
                    }
        return resposta

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao calcular stats últimos N jogos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/players/{player_id}/stats/home-away")
def stats_casa_fora(player_id: int, season: int = Query(2023), location: str = Query(..., description="Casa ou Fora"), db: Session = Depends(get_db)):
    try:
        jogador = db.query(Player).filter(Player.id == player_id).first()
        if not jogador:
            raise HTTPException(status_code=404, detail="Jogador não encontrado")

        if location not in ["home", "away"]:
            raise HTTPException(status_code=400, detail="location deve ser 'home' ou 'away'")

        buscar_home = True
        if location == "away":
            buscar_home = False

        stats_query = (db.query(PlayerGameStats, Game, GameTeamScore).join(Game, PlayerGameStats.game_id == Game.id)
                       .join( GameTeamScore, and_(GameTeamScore.game_id == Game.id, GameTeamScore.team_id == PlayerGameStats.team_id))
                       .filter(PlayerGameStats.player_id == player_id, Game.season == season, Game.status_short == 3, GameTeamScore.is_home == buscar_home).all()
                       )

        if len(stats_query) == 0:
            resposta = {"player_id": player_id, "player_name": f"{jogador.firstname} {jogador.lastname}", "season": season, "location": location, "message": f"Sem dados para jogos {location}"}
            return resposta

        total_points = 0
        total_assists = 0
        total_rebounds = 0
        total_steals = 0
        total_blocks = 0
        total_turnovers = 0
        total_minutes = 0
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

            if stat.points:
                valor = stat.points
                if isinstance(valor, str):
                    valor = int(valor)
                total_points = total_points + valor
                
            if stat.assists:
                valor = stat.assists
                if isinstance(valor, str):
                    valor = int(valor)
                total_assists = total_assists + valor
                
            if stat.tot_reb:
                valor = stat.tot_reb
                if isinstance(valor, str):
                    valor = int(valor)
                total_rebounds = total_rebounds + valor
                
            if stat.steals:
                valor = stat.steals
                if isinstance(valor, str):
                    valor = int(valor)
                total_steals = total_steals + valor
                
            if stat.blocks:
                valor = stat.blocks
                if isinstance(valor, str):
                    valor = int(valor)
                total_blocks = total_blocks + valor
                
            if stat.turnovers:
                valor = stat.turnovers
                if isinstance(valor, str):
                    valor = int(valor)
                total_turnovers = total_turnovers + valor
                
            if stat.minutes:
                valor = stat.minutes
                if isinstance(valor, str):
                    valor = int(valor)
                total_minutes = total_minutes + valor
                
            if stat.fgm:
                valor = stat.fgm
                if isinstance(valor, str):
                    valor = int(valor)
                total_fgm = total_fgm + valor
                
            if stat.fga:
                valor = stat.fga
                if isinstance(valor, str):
                    valor = int(valor)
                total_fga = total_fga + valor
                
            if stat.tpm:
                valor = stat.tpm
                if isinstance(valor, str):
                    valor = int(valor)
                total_tpm = total_tpm + valor
                
            if stat.tpa:
                valor = stat.tpa
                if isinstance(valor, str):
                    valor = int(valor)
                total_tpa = total_tpa + valor
                
            if stat.ftm:
                valor = stat.ftm
                if isinstance(valor, str):
                    valor = int(valor)
                total_ftm = total_ftm + valor
                
            if stat.fta:
                valor = stat.fta
                if isinstance(valor, str):
                    valor = int(valor)
                total_fta = total_fta + valor

            jogo_info = {"game_id": jogo.id, "date": jogo.date_start, "points": stat.points, "assists": stat.assists, "rebounds": stat.tot_reb}
            lista_jogos.append(jogo_info)

        num_jogos = len(stats_query)

        media_points = round(total_points / num_jogos, 2)
        media_assists = round(total_assists / num_jogos, 2)
        media_rebounds = round(total_rebounds / num_jogos, 2)
        media_steals = round(total_steals / num_jogos, 2)
        media_blocks = round(total_blocks / num_jogos, 2)
        media_turnovers = round(total_turnovers / num_jogos, 2)
        media_minutes = round(total_minutes / num_jogos, 2)

        fg_pct = 0
        if total_fga > 0:
            fg_pct = round((total_fgm / total_fga) * 100, 2)
        three_pct = 0
        if total_tpa > 0:
            three_pct = round((total_tpm / total_tpa) * 100, 2)
        ft_pct = 0
        if total_fta > 0:
            ft_pct = round((total_ftm / total_fta) * 100, 2)

        resposta = {
            "player_id": player_id,
            "player_name": f"{jogador.firstname} {jogador.lastname}",
            "season": season,
            "location": location,
            "games_played": num_jogos,
            "averages": {
                "points": media_points,
                "assists": media_assists,
                "rebounds": media_rebounds,
                "steals": media_steals,
                "blocks": media_blocks,
                "turnovers": media_turnovers,
                "minutes": media_minutes,
                "fg_pct": fg_pct,
                "three_pct": three_pct,
                "ft_pct": ft_pct
            },
            "games": lista_jogos
        }
        return resposta

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao calcular stats casa/fora: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/seasons")
def listar_temporadas(db: Session = Depends(get_db)):
    try:
        temporadas = db.query(Season).order_by(Season.season.desc()).all()

        lista_temporadas = []
        for temporada in temporadas:
            temporada_dict = {"season": temporada.season}
            lista_temporadas.append(temporada_dict)

        resposta = {"count": len(lista_temporadas), "seasons": lista_temporadas}
        return resposta

    except Exception as e:
        logger.error(f"Não foi possível listar temporadas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leagues")
def listar_ligas(db: Session = Depends(get_db)):
    try:
        ligas = db.query(League).all()

        lista_ligas = []
        for liga in ligas:
            liga_dict = {"id": liga.id, "code": liga.code, "description": liga.description}
            lista_ligas.append(liga_dict)

        resposta = {"count": len(lista_ligas),"leagues": lista_ligas}
        return resposta

    except Exception as e:
        logger.error(f"Não foi possível listar ligas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/top-scorers")
def top_pontuadores(season: int = Query(2023), limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    try:
        resultados = (db.query(Player.id, Player.firstname, Player.lastname, 
                               func.count(PlayerGameStats.game_id).label("games"),
                               func.sum(PlayerGameStats.points).label("total_points"),
                               func.avg(PlayerGameStats.points).label("avg_points")
                               )
                      .join(PlayerGameStats, Player.id == PlayerGameStats.player_id)
                      .join(Game, PlayerGameStats.game_id == Game.id)
                      .filter(Game.season == season, Game.status_short == 3)
                      .group_by(Player.id, Player.firstname, Player.lastname).order_by(desc("avg_points")).limit(limit).all()
                      )

        lista_scorers = []
        for resultado in resultados:
            player_name = f"{resultado.firstname} {resultado.lastname}"
            avg_points_value = round(float(resultado.avg_points), 2)

            scorer_dict = {"player_id": resultado.id, "player_name": player_name, "games_played": resultado.games,
                           "total_points": resultado.total_points, "avg_points": avg_points_value
                           }
            lista_scorers.append(scorer_dict)

        resposta = {"season": season, "count": len(lista_scorers), "top_scorers": lista_scorers}
        return resposta

    except Exception as e:
        logger.error(f"Não foi possível obter top pontuadores: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/team-trends/{team_id}")
def tendencias_time(team_id: int, season: int = Query(2023), last_n_games: int = Query(10, ge=1, le=20), db: Session = Depends(get_db)):
    try:
        time = db.query(Team).filter(Team.id == team_id).first()
        if not time:
            raise HTTPException(status_code=404, detail="Time não encontrado")

        jogos = (db.query(Game, GameTeamScore).join(GameTeamScore, GameTeamScore.game_id == Game.id)
                 .filter(Game.season == season, GameTeamScore.team_id == team_id, Game.status_short == 3)
                 .order_by(Game.date_start.desc()).limit(last_n_games).all()
                 )

        if len(jogos) == 0:
            resposta = {"team_id": team_id, "team_name": time.name, "message": "Sem jogos finalizados"}
            return resposta

        vitorias = 0
        pontos_feitos = []
        pontos_sofridos = []

        for jogo_data in jogos:
            jogo = jogo_data[0]
            score = jogo_data[1]

            adversario_score = (db.query(GameTeamScore).filter(GameTeamScore.game_id == jogo.id, GameTeamScore.team_id != team_id).first())

            if adversario_score:
                pts_feitos = score.points
                if pts_feitos is None:
                    pts_feitos = 0

                pts_sofridos = adversario_score.points
                if pts_sofridos is None:
                    pts_sofridos = 0

                pontos_feitos.append(pts_feitos)
                pontos_sofridos.append(pts_sofridos)

                if pts_feitos > pts_sofridos:
                    vitorias = vitorias + 1

        num_jogos = len(pontos_feitos)
        derrotas = num_jogos - vitorias

        win_rate = 0
        if num_jogos > 0:
            win_rate = round(vitorias / num_jogos * 100, 2)

        media_pontos_feitos = 0
        if num_jogos > 0:
            soma_feitos = sum(pontos_feitos)
            media_pontos_feitos = round(soma_feitos / num_jogos, 2)

        media_pontos_sofridos = 0
        if num_jogos > 0:
            soma_sofridos = sum(pontos_sofridos)
            media_pontos_sofridos = round(soma_sofridos / num_jogos, 2)

        diferencial = 0
        if num_jogos > 0:
            diferencial = round((sum(pontos_feitos) - sum(pontos_sofridos)) / num_jogos, 2)

        offensive_trend = "stable"
        if len(pontos_feitos) >= 3:
            if pontos_feitos[0] > pontos_feitos[-1]:
                offensive_trend = "improving"
            else:
                offensive_trend = "declining"

        defensive_trend = "stable"
        if len(pontos_sofridos) >= 3:
            if pontos_sofridos[0] < pontos_sofridos[-1]:
                defensive_trend = "improving"
            else:
                defensive_trend = "declining"

        resposta = {
            "team_id": team_id,
            "team_name": time.name,
            "season": season,
            "last_n_games": num_jogos,
            "record": f"{vitorias}-{derrotas}",
            "win_rate": win_rate,
            "avg_points_scored": media_pontos_feitos,
            "avg_points_allowed": media_pontos_sofridos,
            "point_differential": diferencial,
            "offensive_trend": offensive_trend,
            "defensive_trend": defensive_trend
        }
        return resposta

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Não foi possível calcular as tendências do time: {e}")
        raise HTTPException(status_code=500, detail=str(e))