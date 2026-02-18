import logging

from app.services import nba_api_client
from app.db.models import PlayerGameStats, Game, Player
from app.db.db_utils import get_db

from app.etl.func_normalize import _normalizar_string, _normalizar_inteiro

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
   
def carregar_stats_jogador(game_id: int):
    """
    Carrega estatísticas de jogadores para um jogo específico.
    """
    logger.info(f"Iniciando carga de estatísticas para o jogo {game_id}")

    estatistica_jogador = nba_api_client.get_player_statistics(game_id=game_id)

    if estatistica_jogador:
        logger.info(f"API retornou {len(estatistica_jogador)} registros de estatísticas para o jogo {game_id}")
    else:
        logger.warning(f"API retornou resposta vazia para o jogo {game_id}")

    if not estatistica_jogador:
        logger.warning("Sem estatísticas de jogadores para carregar.")
        return

    stats_inseridas = 0
    stats_existentes = 0
    stats_incompletas = 0
    stats_sem_jogador = 0

    for db in get_db():     
        jogo = db.query(Game).filter(Game.id == game_id).first()
        if not jogo:
            logger.error(f"Jogo {game_id} não encontrado na tabela games.")
            return

        season = jogo.season
        if season is None:
            logger.warning(f"Jogo {game_id} encontrado sem temporada definida.")

        for item in estatistica_jogador:
            info_jogador = item.get("player")
            info_franquia = item.get("team")

            id_jogador = info_jogador.get("id") if isinstance(info_jogador, dict) else None
            id_franquia = info_franquia.get("id") if isinstance(info_franquia, dict) else None

            if not id_jogador or not id_franquia:
                logger.warning(f"Dado de jogo incompleto: {item}. Pulando...")
                stats_incompletas += 1
                continue

            jogador_existe_no_db = db.query(Player.id).filter(Player.id == id_jogador).first()
            if not jogador_existe_no_db:
                logger.debug(f"Estatística ignorada: player_id={id_jogador} não existe na tabela players.")
                stats_sem_jogador += 1
                continue

            query_stats = db.query(PlayerGameStats).filter(
                PlayerGameStats.game_id == game_id,
                PlayerGameStats.player_id == id_jogador,
                PlayerGameStats.team_id == id_franquia,
            ).first()

            if query_stats:
                stats_existentes += 1
                continue

            pos = _normalizar_string(item.get("pos"))
            minutes = _normalizar_string(item.get("min"))
            comment = _normalizar_string(item.get("comment"))

            points = _normalizar_inteiro(item.get("points"))
            fgm = _normalizar_inteiro(item.get("fgm"))
            fga = _normalizar_inteiro(item.get("fga"))
            fgp = _normalizar_string(item.get("fgp"))
            ftm = _normalizar_inteiro(item.get("ftm"))
            fta = _normalizar_inteiro(item.get("fta"))
            ftp = _normalizar_string(item.get("ftp"))
            tpm = _normalizar_inteiro(item.get("tpm"))
            tpa = _normalizar_inteiro(item.get("tpa"))
            tpp = _normalizar_string(item.get("tpp"))
            offReb = _normalizar_inteiro(item.get("offReb"))
            defReb = _normalizar_inteiro(item.get("defReb"))
            totReb = _normalizar_inteiro(item.get("totReb"))
            assists = _normalizar_inteiro(item.get("assists"))
            pFouls = _normalizar_inteiro(item.get("pFouls"))
            steals = _normalizar_inteiro(item.get("steals"))
            turnovers = _normalizar_inteiro(item.get("turnovers"))
            blocks = _normalizar_inteiro(item.get("blocks"))
            plusMinus = _normalizar_string(item.get("plusMinus"))

            nova_stats = PlayerGameStats(
                game_id=game_id,
                season=season,
                player_id=id_jogador,
                team_id=id_franquia,
                pos=pos,
                minutes=minutes,
                comment=comment,
                points=points,
                fgm=fgm,
                fga=fga,
                fgp=fgp,
                ftm=ftm,
                fta=fta,
                ftp=ftp,
                tpm=tpm,
                tpa=tpa,
                tpp=tpp,
                off_reb=offReb,
                def_reb=defReb,
                tot_reb=totReb,
                assists=assists,
                p_fouls=pFouls,
                steals=steals,
                turnovers=turnovers,
                blocks=blocks,
                plus_minus=plusMinus,
            )
            db.add(nova_stats)
            stats_inseridas += 1

    logger.info(
        f"Carga de estatísticas para o jogo {game_id} concluída. "
        f"{stats_inseridas} inseridas, {stats_existentes} já existiam, "
        f"{stats_incompletas} incompletas, {stats_sem_jogador} sem FK."
    )


def carregar_stats_todos_jogadores(season: int, team_id: int = None):
    """
    Carrega estatísticas de jogadores em massa para uma temporada.
    """
    logger.info(f"Iniciando carga em massa de estatísticas de jogadores (season={season}, team_id={team_id})...")

    for db in get_db():
        consulta = db.query(Game).filter(Game.season == season)
        if team_id:
            consulta = consulta.filter(
                (Game.home_team_id == team_id) | (Game.away_team_id == team_id)
            )
        jogos = consulta.all()

        if not jogos:
            logger.error("Sem jogos encontrados para carregar estatísticas de jogadores.")
            return

        jogos_processados = 0
        jogos_com_erro = 0
        
        for jogo in jogos:
            try:
                carregar_stats_jogador(game_id=jogo.id)
                jogos_processados += 1
            except Exception as erro:
                logger.error(f"Erro ao carregar estatísticas para o jogo {jogo.id}: {erro}")
                jogos_com_erro += 1
                continue

    logger.info(
        f"Carga em massa de estatísticas concluída. "
        f"{jogos_processados} jogos processados, {jogos_com_erro} com erro."
    )

if __name__ == "__main__":
    carregar_stats_todos_jogadores(season=2023)