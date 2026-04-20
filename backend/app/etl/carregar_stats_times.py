from datetime import datetime, timedelta
import time

from sqlalchemy import or_

from app.services import nba_api_client
from app.db.models import Game, GameTeamStats, Team, TeamSeasonStats
from app.db.db_utils import get_db
from app.etl.func_normalize import _normalizar_string, _normalizar_inteiro, _normalizar_decimal
from app.core.logging_config import configurar_logger

logger = configurar_logger(__name__)

LIGA_NBA_STANDARD = "standard"

def carregar_stats_times_jogo(game_id):
    logger.info(f"Stats times — jogo={game_id}...")
    dados_stats = nba_api_client.get_game_statistics(game_id=game_id)

    if not dados_stats:
        logger.warning(f"API vazia — jogo={game_id}.")
        return

    for db in get_db():
        jogo = db.query(Game).filter(Game.id == game_id).first()

        if not jogo:
            logger.warning(f"Jogo {game_id} nao encontrado.")
            return

        total_inseridos = 0
        total_atualizados = 0

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
                logger.info(f"Atualiza stat time={id_time} jogo={game_id}.")
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
                total_atualizados += 1
                continue

            logger.info(f"Insere stat time={id_time} jogo={game_id}.")
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
            total_inseridos += 1

        db.commit()
        logger.info(f"Fim jogo={game_id} — ins={total_inseridos} atu={total_atualizados}.")

def carregar_stats_todos_times(season, team_id=None, data=None):
    logger.info(f"Stats times em massa — temp={season} data={data}...")

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
            logger.warning(f"Nenhum jogo — temp={season} data={data}.")
            return

        total_jogos = len(jogos)
        logger.info(f"{total_jogos} jogos encontrados — temp={season}.")
        total_erros = 0

        for idx, jogo in enumerate(jogos, start=1):
            logger.info(f"[{idx}/{total_jogos}] Stats times jogo={jogo.id}...")
            try:
                carregar_stats_times_jogo(game_id=jogo.id)
                time.sleep(1)
            except Exception as erro:
                total_erros += 1
                logger.warning(f"[{idx}/{total_jogos}] Erro jogo={jogo.id}: {erro}")
                continue

            if idx % 50 == 0:
                logger.info(f"Progresso: {idx}/{total_jogos} jogos processados ({round(idx/total_jogos*100)}%).")

        if total_erros > 0:
            logger.warning(f"Fim com erros — erros={total_erros} total={total_jogos}.")
        else:
            logger.info(f"Fim — {total_jogos} jogos processados sem erros.")

def carregar_stats_temporada_time(team_id, season):
    logger.info(f"Stats temporada time={team_id} temp={season}...")
    dados = nba_api_client.get_team_statistics(team_id=team_id, season=season, league_id=LIGA_NBA_STANDARD)

    if not dados:
        logger.warning(f"API vazia — time={team_id} temp={season}.")
        return

    if isinstance(dados, list):
        if len(dados) == 0:
            return
        dados = dados[0]

    for db in get_db():
        games_data = dados.get("games", {})
        pontos_for = dados.get("points", {}).get("for", {})

        jogos_total = _normalizar_inteiro(games_data.get("played"))
        fgm = _normalizar_inteiro(dados.get("fgm"))
        fga = _normalizar_inteiro(dados.get("fga"))
        fgp = _normalizar_decimal(dados.get("fgp"))
        ftm = _normalizar_inteiro(dados.get("ftm"))
        fta = _normalizar_inteiro(dados.get("fta"))
        ftp = _normalizar_decimal(dados.get("ftp"))
        tpm = _normalizar_inteiro(dados.get("tpm"))
        tpa = _normalizar_inteiro(dados.get("tpa"))
        tpp = _normalizar_decimal(dados.get("tpp"))
        off_reb = _normalizar_inteiro(dados.get("offReb"))
        def_reb = _normalizar_inteiro(dados.get("defReb"))
        tot_reb = _normalizar_inteiro(dados.get("totReb"))
        assists = _normalizar_inteiro(dados.get("assists"))
        p_fouls = _normalizar_inteiro(dados.get("pFouls"))
        steals = _normalizar_inteiro(dados.get("steals"))
        turnovers = _normalizar_inteiro(dados.get("turnovers"))
        blocks = _normalizar_inteiro(dados.get("blocks"))
        plus_minus = _normalizar_inteiro(dados.get("plusMinus"))
        fast_break_points = _normalizar_inteiro(dados.get("fastBreakPoints"))
        points_in_paint = _normalizar_inteiro(dados.get("pointsInPaint"))
        biggest_lead = _normalizar_inteiro(dados.get("biggestLead"))
        second_chance_points = _normalizar_inteiro(dados.get("secondChancePoints"))
        points_off_turnovers = _normalizar_inteiro(dados.get("pointsOffTurnovers"))
        longest_run = _normalizar_inteiro(dados.get("longestRun"))

        if isinstance(pontos_for, dict):
            total_pts_obj = pontos_for.get("total", {})
            if isinstance(total_pts_obj, dict):
                pontos_total = _normalizar_inteiro(total_pts_obj.get("all"))
            else:
                pontos_total = _normalizar_inteiro(total_pts_obj)
        else:
            pontos_total = _normalizar_inteiro(dados.get("points"))

        stats_existente = db.query(TeamSeasonStats).filter(TeamSeasonStats.team_id == team_id, TeamSeasonStats.season == season).first()

        if stats_existente:
            logger.info(f"Atualiza stats temporada time={team_id}.")
            stats_existente.games = jogos_total
            stats_existente.points = pontos_total
            stats_existente.fgm = fgm
            stats_existente.fga = fga
            stats_existente.fgp = fgp
            stats_existente.ftm = ftm
            stats_existente.fta = fta
            stats_existente.ftp = ftp
            stats_existente.tpm = tpm
            stats_existente.tpa = tpa
            stats_existente.tpp = tpp
            stats_existente.off_reb = off_reb
            stats_existente.def_reb = def_reb
            stats_existente.tot_reb = tot_reb
            stats_existente.assists = assists
            stats_existente.p_fouls = p_fouls
            stats_existente.steals = steals
            stats_existente.turnovers = turnovers
            stats_existente.blocks = blocks
            stats_existente.plus_minus = plus_minus
            stats_existente.fast_break_points = fast_break_points
            stats_existente.points_in_paint = points_in_paint
            stats_existente.biggest_lead = biggest_lead
            stats_existente.second_chance_points = second_chance_points
            stats_existente.points_off_turnovers = points_off_turnovers
            stats_existente.longest_run = longest_run
        else:
            logger.info(f"Insere stats temporada time={team_id}.")
            nova_stat = TeamSeasonStats(
                team_id=team_id, season=season,
                games=jogos_total, points=pontos_total,
                fgm=fgm, fga=fga, fgp=fgp,
                ftm=ftm, fta=fta, ftp=ftp,
                tpm=tpm, tpa=tpa, tpp=tpp,
                off_reb=off_reb, def_reb=def_reb, tot_reb=tot_reb,
                assists=assists, p_fouls=p_fouls, steals=steals,
                turnovers=turnovers, blocks=blocks, plus_minus=plus_minus,
                fast_break_points=fast_break_points, points_in_paint=points_in_paint,
                biggest_lead=biggest_lead, second_chance_points=second_chance_points,
                points_off_turnovers=points_off_turnovers, longest_run=longest_run,
            )
            db.add(nova_stat)

        db.commit()
        logger.info(f"Fim stats temporada time={team_id}.")

def carregar_stats_temporada_todos_times(season):
    logger.info(f"Stats temporada todos times — temp={season}...")

    for db in get_db():
        times = db.query(Team).filter(Team.nba_franchise == True).all()

        if not times:
            logger.warning("Nenhum time NBA no banco.")
            return

        logger.info(f"{len(times)} times encontrados.")
        total_ok = 0

        for time in times:
            try:
                carregar_stats_temporada_time(team_id=time.id, season=season)
                total_ok += 1
            except Exception as erro:
                logger.warning(f"Erro time={time.id}: {erro}")
                continue

        logger.info(f"Fim — ok={total_ok} total={len(times)}.")

if __name__ == "__main__":
    carregar_stats_todos_times(season=2025)
    carregar_stats_temporada_todos_times(season=2025)