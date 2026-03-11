import logging
from datetime import datetime, timedelta

from app.services import nba_api_client
from app.db.models import PlayerGameStats, Game, Player
from app.db.db_utils import get_db
from app.etl.func_normalize import _normalizar_string, _normalizar_inteiro, _normalizar_decimal

logger = logging.getLogger(__name__)

def carregar_stats_jogador(game_id):
    estatistica_jogador = nba_api_client.get_player_statistics(game_id=game_id)

    if not estatistica_jogador:
        logger.warning(f"Nenhuma estatística retornada pela API para game_id={game_id}")
        return

    for db in get_db():
        jogo = db.query(Game).filter(Game.id == game_id).first()

        if not jogo:
            logger.warning(f"Jogo não encontrado no banco —> game_id={game_id}")
            return

        season = jogo.season

        for item in estatistica_jogador:
            info_jogador = item.get("player")
            info_franquia = item.get("team")

            if isinstance(info_jogador, dict):
                id_jogador = _normalizar_inteiro(info_jogador.get("id"))
            else:
                id_jogador = None

            if isinstance(info_franquia, dict):
                id_franquia = _normalizar_inteiro(info_franquia.get("id"))
            else:
                id_franquia = None

            if not id_jogador or not id_franquia:
                continue

            jogador_existe_no_db = db.query(Player.id).filter(Player.id == id_jogador).first()

            if not jogador_existe_no_db:
                continue

            stats_existente = db.query(PlayerGameStats).filter(PlayerGameStats.game_id == game_id, PlayerGameStats.player_id == id_jogador, PlayerGameStats.team_id == id_franquia).first()

            if stats_existente:
                stats_existente.pos = _normalizar_string(item.get("pos"))
                stats_existente.minutes = _normalizar_string(item.get("min"))
                stats_existente.comment = _normalizar_string(item.get("comment"))
                stats_existente.points = _normalizar_inteiro(item.get("points"))
                stats_existente.fgm = _normalizar_inteiro(item.get("fgm"))
                stats_existente.fga = _normalizar_inteiro(item.get("fga"))
                stats_existente.fgp = _normalizar_decimal(item.get("fgp"))
                stats_existente.ftm = _normalizar_inteiro(item.get("ftm"))
                stats_existente.fta = _normalizar_inteiro(item.get("fta"))
                stats_existente.ftp = _normalizar_decimal(item.get("ftp"))
                stats_existente.tpm = _normalizar_inteiro(item.get("tpm"))
                stats_existente.tpa = _normalizar_inteiro(item.get("tpa"))
                stats_existente.tpp = _normalizar_decimal(item.get("tpp"))
                stats_existente.off_reb = _normalizar_inteiro(item.get("offReb"))
                stats_existente.def_reb = _normalizar_inteiro(item.get("defReb"))
                stats_existente.tot_reb = _normalizar_inteiro(item.get("totReb"))
                stats_existente.assists = _normalizar_inteiro(item.get("assists"))
                stats_existente.p_fouls = _normalizar_inteiro(item.get("pFouls"))
                stats_existente.steals = _normalizar_inteiro(item.get("steals"))
                stats_existente.turnovers = _normalizar_inteiro(item.get("turnovers"))
                stats_existente.blocks = _normalizar_inteiro(item.get("blocks"))
                stats_existente.plus_minus = _normalizar_inteiro(item.get("plusMinus"))
                continue

            nova_stats = PlayerGameStats(
                game_id=game_id,
                season=season,
                player_id=id_jogador,
                team_id=id_franquia,
                pos=_normalizar_string(item.get("pos")),
                minutes=_normalizar_string(item.get("min")),
                comment=_normalizar_string(item.get("comment")),
                points=_normalizar_inteiro(item.get("points")),
                fgm=_normalizar_inteiro(item.get("fgm")),
                fga=_normalizar_inteiro(item.get("fga")),
                fgp=_normalizar_decimal(item.get("fgp")),
                ftm=_normalizar_inteiro(item.get("ftm")),
                fta=_normalizar_inteiro(item.get("fta")),
                ftp=_normalizar_decimal(item.get("ftp")),
                tpm=_normalizar_inteiro(item.get("tpm")),
                tpa=_normalizar_inteiro(item.get("tpa")),
                tpp=_normalizar_decimal(item.get("tpp")),
                off_reb=_normalizar_inteiro(item.get("offReb")),
                def_reb=_normalizar_inteiro(item.get("defReb")),
                tot_reb=_normalizar_inteiro(item.get("totReb")),
                assists=_normalizar_inteiro(item.get("assists")),
                p_fouls=_normalizar_inteiro(item.get("pFouls")),
                steals=_normalizar_inteiro(item.get("steals")),
                turnovers=_normalizar_inteiro(item.get("turnovers")),
                blocks=_normalizar_inteiro(item.get("blocks")),
                plus_minus=_normalizar_inteiro(item.get("plusMinus")),
            )
            db.add(nova_stats)

def carregar_stats_todos_jogadores(season, team_id=None, data=None):
    for db in get_db():
        consulta = db.query(Game).filter(Game.season == season)

        if team_id:
            consulta = consulta.filter((Game.home_team_id == team_id) | (Game.away_team_id == team_id))

        if data:
            data_inicio = datetime.strptime(data, "%Y-%m-%d")
            data_fim = data_inicio + timedelta(days=1)
            consulta = consulta.filter(Game.date_start >= data_inicio, Game.date_start < data_fim)

        jogos = consulta.all()

        if not jogos:
            logger.warning(f"Nenhum jogo encontrado no banco —> season={season}, team_id={team_id}, data={data}")
            return

        total_jogos = len(jogos)
        total_erros = 0

        for jogo in jogos:
            try:
                carregar_stats_jogador(game_id=jogo.id)
            except Exception as erro:
                total_erros = total_erros + 1
                logger.warning(f"Falha ao carregar stats de jogadores do jogo {jogo.id}: {erro}")
                continue

        if total_erros > 0:
            logger.warning(f"Carga concluída com erros —> season={season}, total_jogos={total_jogos}, erros={total_erros}")

if __name__ == "__main__":
    carregar_stats_todos_jogadores(season=2025)