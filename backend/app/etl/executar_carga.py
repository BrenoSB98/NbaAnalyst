import argparse
import logging

from app.etl.carregar_ligas import carregar_ligas
from app.etl.carregar_temporadas import carregar_temporadas
from app.etl.carregar_franquias import carregar_times
from app.etl.carregar_jogadores import carregar_jogadores
from app.etl.carregar_jogadores_franquias import carregar_jogadores_franquias
from app.etl.carregar_partidas import carregar_partidas
from app.etl.carregar_stats_jogadores import carregar_stats_jogador, carregar_stats_todos_jogadores

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """
    Ponto de entrada para execução do processo de ETL da NBA.
    """
    parser = argparse.ArgumentParser(description="Executa o processo de ETL para dados da NBA.")
    parser.add_argument(
        "--season",
        type=int,
        required=False,
        help="Ano da temporada"
    )

    parser.add_argument(
        "--load",
        type=str,
        choices=[
            "temporadas",
            "ligas",
            "times",
            "jogadores",
            "jogadores_times",
            "partidas",
            "stats_jogador",
            "stats_jogador_massa",
            "all"
        ],
        required=True,
        help="Escolha o tipo de dado a ser carregado"
    )

    parser.add_argument(
        "--team_id",
        dest="team_id",
        type=int,
        required=False,
        help="ID do time para carregar jogadores específicos"
    )

    parser.add_argument(
        "--date",
        type=str,
        required=False,
        help="Data para carregar jogos (formato: YYYY-MM-DD).",
    )

    parser.add_argument(
        "--game_id",
        dest="game_id",
        type=int,
        required=False,
        help="ID do jogo para carregar estatísticas de jogadores.",
    )

    args = parser.parse_args()

    if args.load == "temporadas":
        carregar_temporadas()

    elif args.load == "ligas":
        carregar_ligas()

    elif args.load == "times":
        carregar_times()

    elif args.load == "jogadores":
        if not args.season and not args.team_id:
            logger.error("Para carregar jogadores, tanto 'season' quanto 'team_id' devem ser fornecidos.")
            return
        carregar_jogadores(team_id=args.team_id, season=args.season)

    elif args.load == "jogadores_times":
        if not args.season:
            logger.error("Para carregar jogadores por time, 'season' deve ser fornecido.")
            return
        carregar_jogadores_franquias(season=args.season)

    elif args.load == "partidas":
        if not args.season:
            logger.error("Para carregar partidas é necessário informar --season.")
            return
        carregar_partidas(season=args.season, date=args.date, team_id=args.team_id)

    elif args.load == "stats_jogador":
        if not args.game_id:
            logger.error("Para carregar stats_jogador é necessário informar --game_id.")
            return
        carregar_stats_jogador(game_id=args.game_id)

    elif args.load == "stats_jogador_massa":
        if not args.season:
            logger.error("Para carregar stats_jogador_massa é necessário informar --season.")
            return
        carregar_stats_todos_jogadores(season=args.season, team_id=args.team_id)

    elif args.load == "all":
        carregar_temporadas()
        carregar_ligas()
        carregar_times()
        carregar_jogadores_franquias(season=args.season)
        carregar_partidas(season=args.season, date=args.date, team_id=args.team_id)
        carregar_stats_todos_jogadores(season=args.season)


if __name__ == "__main__":
    main()