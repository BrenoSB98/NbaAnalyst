from sqlalchemy import or_

from app.services import nba_api_client
from app.db.models import Game, GameTeamStats, Team
from app.db.db_utils import get_db
from app.etl.func_normalize import _normalizar_string, _normalizar_inteiro, _normalizar_decimal

def carregar_stats_times_jogo(game_id):
    dados_stats = nba_api_client.get_game_statistics(game_id=game_id)

    if not dados_stats:
        return

    for db in get_db():
        jogo = db.query(Game).filter(Game.id == game_id).first()
        if not jogo:
            return

        for item in dados_stats:
            info_time = item.get("team")
            if not isinstance(info_time, dict):
                continue

            id_time = _normalizar_inteiro(info_time.get("id"))
            if not id_time:
                continue

            time_existe = db.query(Team).filter(Team.id == id_time).first()
            if not time_existe:
                continue

            stats_existente = db.query(GameTeamStats).filter(GameTeamStats.game_id == game_id, GameTeamStats.team_id == id_time).first()

            if stats_existente:
                continue

            estatisticas = item.get("statistics")
            if isinstance(estatisticas, list) and len(estatisticas) > 0:
                estatisticas = estatisticas[0]
            elif not isinstance(estatisticas, dict):
                continue

            nova_stat = GameTeamStats(
                game_id=game_id,
                team_id=id_time,
                fast_break_points=_normalizar_inteiro(estatisticas.get("fastBreakPoints")),
                points_in_paint=_normalizar_inteiro(estatisticas.get("pointsInPaint")),
                biggest_lead=_normalizar_inteiro(estatisticas.get("biggestLead")),
                second_chance_points=_normalizar_inteiro(estatisticas.get("secondChancePoints")),
                points_off_turnovers=_normalizar_inteiro(estatisticas.get("pointsOffTurnovers")),
                longest_run=_normalizar_inteiro(estatisticas.get("longestRun")),
                points=_normalizar_inteiro(estatisticas.get("points")),
                fgm=_normalizar_inteiro(estatisticas.get("fgm")),
                fga=_normalizar_inteiro(estatisticas.get("fga")),
                fgp=_normalizar_decimal(estatisticas.get("fgp")),
                ftm=_normalizar_inteiro(estatisticas.get("ftm")),
                fta=_normalizar_inteiro(estatisticas.get("fta")),
                ftp=_normalizar_decimal(estatisticas.get("ftp")),
                tpm=_normalizar_inteiro(estatisticas.get("tpm")),
                tpa=_normalizar_inteiro(estatisticas.get("tpa")),
                tpp=_normalizar_decimal(estatisticas.get("tpp")),
                off_reb=_normalizar_inteiro(estatisticas.get("offReb")),
                def_reb=_normalizar_inteiro(estatisticas.get("defReb")),
                tot_reb=_normalizar_inteiro(estatisticas.get("totReb")),
                assists=_normalizar_inteiro(estatisticas.get("assists")),
                p_fouls=_normalizar_inteiro(estatisticas.get("pFouls")),
                steals=_normalizar_inteiro(estatisticas.get("steals")),
                turnovers=_normalizar_inteiro(estatisticas.get("turnovers")),
                blocks=_normalizar_inteiro(estatisticas.get("blocks")),
                plus_minus=_normalizar_inteiro(estatisticas.get("plusMinus")),
                minutes=_normalizar_string(estatisticas.get("min")),
            )
            db.add(nova_stat)

def carregar_stats_todos_times(season, team_id=None):
    for db in get_db():
        consulta = db.query(Game).filter(Game.season == season)

        if team_id:
            consulta = consulta.filter(or_(Game.home_team_id == team_id, Game.away_team_id == team_id))

        jogos = consulta.all()

        if not jogos:
            return

        for jogo in jogos:
            try:
                carregar_stats_times_jogo(game_id=jogo.id)
            except Exception:
                continue

if __name__ == "__main__":
    carregar_stats_todos_times(season=2023)