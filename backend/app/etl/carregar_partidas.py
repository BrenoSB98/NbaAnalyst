import logging

from app.services import nba_api_client
from app.db.models import Game, GameTeamScore, Team
from app.db.db_utils import get_db
from app.etl.func_normalize import _normalizar_string, _normalizar_inteiro, _normalizar_boolean, _processar_datetime

logger = logging.getLogger(__name__)

def carregar_partidas(season, date=None, team_id=None, league_id=None):
    dados_jogos = nba_api_client.get_games(season=season, date=date, team_id=team_id, league_id=league_id)

    if not dados_jogos:
        logger.warning(f"Nenhum jogo retornado pela API —> season={season}, date={date}, team_id={team_id}")
        return

    for db in get_db():
        for item in dados_jogos:
            game_id = _normalizar_inteiro(item.get("id") or item.get("gameId"))

            if not game_id:
                continue

            liga = _normalizar_string(item.get("league"))
            estagio = _normalizar_string(item.get("stage"))

            date_info = item.get("date", {})
            data_inicio = date_info.get("start")
            data_fim = date_info.get("end")
            duracao = _normalizar_string(date_info.get("duration"))

            status = item.get("status", {})
            status_curto = _normalizar_inteiro(status.get("short"))
            status_longo = _normalizar_string(status.get("long"))

            periodos = item.get("periods", {})
            periodo_atual = _normalizar_inteiro(periodos.get("current"))
            total_periodos = _normalizar_inteiro(periodos.get("total"))
            fim_de_periodo = _normalizar_boolean(periodos.get("endOfPeriod"))

            arena = item.get("arena", {})
            nome_arena = _normalizar_string(arena.get("name"))
            cidade_arena = _normalizar_string(arena.get("city"))
            estado_arena = _normalizar_string(arena.get("state"))
            pais_arena = _normalizar_string(arena.get("country"))

            times = item.get("teams", {})
            info_time_casa = times.get("home", {})
            info_time_visitante = times.get("visitors", {}) or times.get("away", {})

            id_time_casa = _normalizar_inteiro(info_time_casa.get("id"))
            id_time_visitante = _normalizar_inteiro(info_time_visitante.get("id"))

            placares = item.get("scores", {})
            placar_casa = placares.get("home", {})
            placar_visitante = placares.get("visitors", {}) or placares.get("away", {})

            linescore_casa = placar_casa.get("linescore", [])
            linescore_visitante = placar_visitante.get("linescore", [])

            serie_casa = placar_casa.get("series", {})
            serie_visitante = placar_visitante.get("series", {})

            data_inicio_obj = _processar_datetime(data_inicio)
            data_fim_obj = _processar_datetime(data_fim)

            jogo_existente = db.query(Game).filter(Game.id == game_id).first()

            if jogo_existente:
                jogo_existente.status_short = status_curto
                jogo_existente.status_long = status_longo
                jogo_existente.periods_current = periodo_atual
                jogo_existente.periods_end_of_period = fim_de_periodo
                jogo_existente.date_end = data_fim_obj
                jogo_existente.duration = duracao

                _atualizar_placares_jogo(db=db, game_id=game_id, placar_casa=placar_casa, placar_visitante=placar_visitante,
                                         id_time_casa=id_time_casa, id_time_visitante=id_time_visitante,
                                         linescore_casa=linescore_casa, linescore_visitante=linescore_visitante,
                                         serie_casa=serie_casa, serie_visitante=serie_visitante)
                continue

            if not id_time_casa or not id_time_visitante:
                logger.warning(f"Jogo {game_id} ignorado —> IDs de times ausentes: casa={id_time_casa}, visitante={id_time_visitante}")
                continue

            time_casa_existe = db.query(Team.id).filter(Team.id == id_time_casa).first()
            time_visitante_existe = db.query(Team.id).filter(Team.id == id_time_visitante).first()

            if not time_casa_existe or not time_visitante_existe:
                logger.warning(f"Jogo {game_id} ignorado —> time não cadastrado no banco: casa={id_time_casa}, visitante={id_time_visitante}")
                continue

            if not data_inicio_obj:
                logger.warning(f"Jogo {game_id} ignorado —> data_start inválida ou ausente: '{data_inicio}'")
                continue

            novo_jogo = Game(
                id=game_id,
                league=liga,
                season=season,
                date_start=data_inicio_obj,
                date_end=data_fim_obj,
                duration=duracao,
                stage=estagio,
                status_short=status_curto,
                status_long=status_longo,
                periods_current=periodo_atual,
                periods_total=total_periodos,
                periods_end_of_period=fim_de_periodo,
                arena_name=nome_arena,
                arena_city=cidade_arena,
                arena_state=estado_arena,
                arena_country=pais_arena,
                home_team_id=id_time_casa,
                away_team_id=id_time_visitante,
            )
            db.add(novo_jogo)

            placar_time_casa = GameTeamScore(
                game_id=game_id,
                team_id=id_time_casa,
                is_home=True,
                win=_normalizar_inteiro(placar_casa.get("win")),
                loss=_normalizar_inteiro(placar_casa.get("loss")),
                series_win=_normalizar_inteiro(serie_casa.get("win")),
                series_loss=_normalizar_inteiro(serie_casa.get("loss")),
                points=_normalizar_inteiro(placar_casa.get("points")),
                linescore_q1=_normalizar_inteiro(linescore_casa[0]) if len(linescore_casa) > 0 else None,
                linescore_q2=_normalizar_inteiro(linescore_casa[1]) if len(linescore_casa) > 1 else None,
                linescore_q3=_normalizar_inteiro(linescore_casa[2]) if len(linescore_casa) > 2 else None,
                linescore_q4=_normalizar_inteiro(linescore_casa[3]) if len(linescore_casa) > 3 else None,
            )
            db.add(placar_time_casa)

            placar_time_visitante = GameTeamScore(
                game_id=game_id,
                team_id=id_time_visitante,
                is_home=False,
                win=_normalizar_inteiro(placar_visitante.get("win")),
                loss=_normalizar_inteiro(placar_visitante.get("loss")),
                series_win=_normalizar_inteiro(serie_visitante.get("win")),
                series_loss=_normalizar_inteiro(serie_visitante.get("loss")),
                points=_normalizar_inteiro(placar_visitante.get("points")),
                linescore_q1=_normalizar_inteiro(linescore_visitante[0]) if len(linescore_visitante) > 0 else None,
                linescore_q2=_normalizar_inteiro(linescore_visitante[1]) if len(linescore_visitante) > 1 else None,
                linescore_q3=_normalizar_inteiro(linescore_visitante[2]) if len(linescore_visitante) > 2 else None,
                linescore_q4=_normalizar_inteiro(linescore_visitante[3]) if len(linescore_visitante) > 3 else None,
            )
            db.add(placar_time_visitante)

def _atualizar_placares_jogo(db, game_id, placar_casa, placar_visitante, id_time_casa, id_time_visitante, linescore_casa, linescore_visitante, serie_casa, serie_visitante):
    placar_casa_existente = db.query(GameTeamScore).filter(GameTeamScore.game_id == game_id, GameTeamScore.team_id == id_time_casa).first()

    if placar_casa_existente:
        placar_casa_existente.win = _normalizar_inteiro(placar_casa.get("win"))
        placar_casa_existente.loss = _normalizar_inteiro(placar_casa.get("loss"))
        placar_casa_existente.series_win = _normalizar_inteiro(serie_casa.get("win"))
        placar_casa_existente.series_loss = _normalizar_inteiro(serie_casa.get("loss"))
        placar_casa_existente.points = _normalizar_inteiro(placar_casa.get("points"))
        placar_casa_existente.linescore_q1 = _normalizar_inteiro(linescore_casa[0]) if len(linescore_casa) > 0 else None
        placar_casa_existente.linescore_q2 = _normalizar_inteiro(linescore_casa[1]) if len(linescore_casa) > 1 else None
        placar_casa_existente.linescore_q3 = _normalizar_inteiro(linescore_casa[2]) if len(linescore_casa) > 2 else None
        placar_casa_existente.linescore_q4 = _normalizar_inteiro(linescore_casa[3]) if len(linescore_casa) > 3 else None
    else:
        novo_placar_casa = GameTeamScore(
            game_id=game_id,
            team_id=id_time_casa,
            is_home=True,
            win=_normalizar_inteiro(placar_casa.get("win")),
            loss=_normalizar_inteiro(placar_casa.get("loss")),
            series_win=_normalizar_inteiro(serie_casa.get("win")),
            series_loss=_normalizar_inteiro(serie_casa.get("loss")),
            points=_normalizar_inteiro(placar_casa.get("points")),
            linescore_q1=_normalizar_inteiro(linescore_casa[0]) if len(linescore_casa) > 0 else None,
            linescore_q2=_normalizar_inteiro(linescore_casa[1]) if len(linescore_casa) > 1 else None,
            linescore_q3=_normalizar_inteiro(linescore_casa[2]) if len(linescore_casa) > 2 else None,
            linescore_q4=_normalizar_inteiro(linescore_casa[3]) if len(linescore_casa) > 3 else None,
        )
        db.add(novo_placar_casa)

    placar_visitante_existente = db.query(GameTeamScore).filter(GameTeamScore.game_id == game_id, GameTeamScore.team_id == id_time_visitante).first()

    if placar_visitante_existente:
        placar_visitante_existente.win = _normalizar_inteiro(placar_visitante.get("win"))
        placar_visitante_existente.loss = _normalizar_inteiro(placar_visitante.get("loss"))
        placar_visitante_existente.series_win = _normalizar_inteiro(serie_visitante.get("win"))
        placar_visitante_existente.series_loss = _normalizar_inteiro(serie_visitante.get("loss"))
        placar_visitante_existente.points = _normalizar_inteiro(placar_visitante.get("points"))
        placar_visitante_existente.linescore_q1 = _normalizar_inteiro(linescore_visitante[0]) if len(linescore_visitante) > 0 else None
        placar_visitante_existente.linescore_q2 = _normalizar_inteiro(linescore_visitante[1]) if len(linescore_visitante) > 1 else None
        placar_visitante_existente.linescore_q3 = _normalizar_inteiro(linescore_visitante[2]) if len(linescore_visitante) > 2 else None
        placar_visitante_existente.linescore_q4 = _normalizar_inteiro(linescore_visitante[3]) if len(linescore_visitante) > 3 else None
    else:
        novo_placar_visitante = GameTeamScore(
            game_id=game_id,
            team_id=id_time_visitante,
            is_home=False,
            win=_normalizar_inteiro(placar_visitante.get("win")),
            loss=_normalizar_inteiro(placar_visitante.get("loss")),
            series_win=_normalizar_inteiro(serie_visitante.get("win")),
            series_loss=_normalizar_inteiro(serie_visitante.get("loss")),
            points=_normalizar_inteiro(placar_visitante.get("points")),
            linescore_q1=_normalizar_inteiro(linescore_visitante[0]) if len(linescore_visitante) > 0 else None,
            linescore_q2=_normalizar_inteiro(linescore_visitante[1]) if len(linescore_visitante) > 1 else None,
            linescore_q3=_normalizar_inteiro(linescore_visitante[2]) if len(linescore_visitante) > 2 else None,
            linescore_q4=_normalizar_inteiro(linescore_visitante[3]) if len(linescore_visitante) > 3 else None,
        )
        db.add(novo_placar_visitante)

if __name__ == "__main__":
    carregar_partidas(season=2025)