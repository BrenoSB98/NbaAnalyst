import logging
from datetime import datetime, timedelta

from sqlalchemy import or_

from app.services import nba_api_client
from app.db.models import Game, GameTeamStats, Team
from app.db.db_utils import get_db
from app.etl.func_normalize import _normalizar_string, _normalizar_inteiro, _normalizar_decimal

logger = logging.getLogger(__name__)

def carregar_stats_times_jogo(game_id):
    dados_stats = nba_api_client.get_game_statistics(game_id=game_id)

    if not dados_stats:
        logger.warning(f"Nenhuma estatística retornada pela API para jogo={game_id}")
        return

    for db in get_db():
        jogo = db.query(Game).filter(Game.id == game_id).first()

        if not jogo:
            logger.warning(f"Jogo não encontrado —> jogo={game_id}")
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
            estatisticas = item.get("statistics")

            if isinstance(estatisticas, list) and len(estatisticas) > 0:
                estatisticas = estatisticas[0]
            elif not isinstance(estatisticas, dict):
                continue

            stats_existente = db.query(GameTeamStats).filter(GameTeamStats.game_id == game_id, GameTeamStats.team_id == id_time).first()
            if stats_existente:
                stats_existente.fast_break_points = _normalizar_inteiro(estatisticas.get("fastBreakPoints"))
                stats_existente.points_in_paint = _normalizar_inteiro(estatisticas.get("pointsInPaint"))
                stats_existente.biggest_lead = _normalizar_inteiro(estatisticas.get("biggestLead"))
                stats_existente.second_chance_points = _normalizar_inteiro(estatisticas.get("secondChancePoints"))
                stats_existente.points_off_turnovers = _normalizar_inteiro(estatisticas.get("pointsOffTurnovers"))
                stats_existente.longest_run = _normalizar_inteiro(estatisticas.get("longestRun"))
                stats_existente.points = _normalizar_inteiro(estatisticas.get("points"))
                stats_existente.fgm = _normalizar_inteiro(estatisticas.get("fgm"))
                stats_existente.fga = _normalizar_inteiro(estatisticas.get("fga"))
                stats_existente.fgp = _normalizar_decimal(estatisticas.get("fgp"))
                stats_existente.ftm = _normalizar_inteiro(estatisticas.get("ftm"))
                stats_existente.fta = _normalizar_inteiro(estatisticas.get("fta"))
                stats_existente.ftp = _normalizar_decimal(estatisticas.get("ftp"))
                stats_existente.tpm = _normalizar_inteiro(estatisticas.get("tpm"))
                stats_existente.tpa = _normalizar_inteiro(estatisticas.get("tpa"))
                stats_existente.tpp = _normalizar_decimal(estatisticas.get("tpp"))
                stats_existente.off_reb = _normalizar_inteiro(estatisticas.get("offReb"))
                stats_existente.def_reb = _normalizar_inteiro(estatisticas.get("defReb"))
                stats_existente.tot_reb = _normalizar_inteiro(estatisticas.get("totReb"))
                stats_existente.assists = _normalizar_inteiro(estatisticas.get("assists"))
                stats_existente.p_fouls = _normalizar_inteiro(estatisticas.get("pFouls"))
                stats_existente.steals = _normalizar_inteiro(estatisticas.get("steals"))
                stats_existente.turnovers = _normalizar_inteiro(estatisticas.get("turnovers"))
                stats_existente.blocks = _normalizar_inteiro(estatisticas.get("blocks"))
                stats_existente.plus_minus = _normalizar_inteiro(estatisticas.get("plusMinus"))
                stats_existente.minutes = _normalizar_string(estatisticas.get("min"))
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

def carregar_stats_todos_times(season, team_id=None, data=None):
    for db in get_db():
        consulta = db.query(Game).filter(Game.season == season)

        if team_id:
            consulta = consulta.filter(or_(Game.home_team_id == team_id, Game.away_team_id == team_id))

        if data:
            data_inicio = datetime.strptime(data, "%Y-%m-%d")
            data_fim = data_inicio + timedelta(days=1)
            consulta = consulta.filter(Game.date_start >= data_inicio, Game.date_start < data_fim)

        jogos = consulta.all()
        if not jogos:
            logger.warning(f"Nenhum jogo encontrado —> temporada={season}, franquia={team_id}, data={data}")
            return

        total_jogos = len(jogos)
        total_erros = 0

        for jogo in jogos:
            try:
                carregar_stats_times_jogo(game_id=jogo.id)
            except Exception as erro:
                total_erros += 1
                logger.warning(f"Falha ao carregar estatistica do jogo {jogo.id}: {erro}")
                continue

        if total_erros > 0:
            logger.warning(f"Carga concluída com erros —> temporada={season}, total_jogos={total_jogos}, erros={total_erros}")

if __name__ == "__main__":
    carregar_stats_todos_times(season=2025)