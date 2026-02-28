import argparse
import sys

from app.etl.carregar_ligas import carregar_ligas
from app.etl.carregar_temporadas import carregar_temporadas
from app.etl.carregar_franquias import carregar_times
from app.etl.carregar_jogadores import carregar_jogadores
from app.etl.carregar_jogadores_franquias import carregar_jogadores_franquias
from app.etl.carregar_partidas import carregar_partidas
from app.etl.carregar_stats_jogadores import carregar_stats_jogador, carregar_stats_todos_jogadores
from app.etl.carregar_stats_times import carregar_stats_times_jogo, carregar_stats_todos_times

def main():
    parser = argparse.ArgumentParser(description="Script para executar cargas de dados na base de dados NBA.")
    parser.add_argument("--season", type=int, required=False, help="Ano da temporada")
    parser.add_argument(
        "--load",
        type=str,
        choices=[
            "temporadas", "ligas", "times", "jogadores", "jogadores_times",
            "partidas", "stats_jogador", "stats_jogador_massa",
            "stats_times", "stats_times_massa", "all"
        ],
        required=True,
        help="Escolha o tipo de dado a ser carregado"
    )
    parser.add_argument("--team_id", dest="team_id", type=int, required=False, help="ID do time")
    parser.add_argument("--date", type=str, required=False, help="Data para carregar jogos (formato: YYYY-MM-DD).")
    parser.add_argument("--game_id", dest="game_id", type=int, required=False, help="ID do jogo.")

    args = parser.parse_args()

    if args.load == "temporadas":
        carregar_temporadas()

    elif args.load == "ligas":
        carregar_ligas()

    elif args.load == "times":
        carregar_times()

    elif args.load == "jogadores":
        if not args.season and not args.team_id:
            sys.exit(1)
        carregar_jogadores(team_id=args.team_id, season=args.season)

    elif args.load == "jogadores_times":
        if not args.season:
            sys.exit(1)
        carregar_jogadores_franquias(season=args.season)

    elif args.load == "partidas":
        if not args.season:
            sys.exit(1)
        carregar_partidas(season=args.season, date=args.date, team_id=args.team_id)

    elif args.load == "stats_jogador":
        if not args.game_id:
            sys.exit(1)
        carregar_stats_jogador(game_id=args.game_id)

    elif args.load == "stats_jogador_massa":
        if not args.season:
            sys.exit(1)
        carregar_stats_todos_jogadores(season=args.season, team_id=args.team_id)

    elif args.load == "stats_times":
        if not args.game_id:
            sys.exit(1)
        carregar_stats_times_jogo(game_id=args.game_id)

    elif args.load == "stats_times_massa":
        if not args.season:
            sys.exit(1)
        carregar_stats_todos_times(season=args.season, team_id=args.team_id)

    elif args.load == "all":
        carregar_temporadas()
        carregar_ligas()
        carregar_times()
        carregar_jogadores_franquias(season=args.season)
        carregar_partidas(season=args.season, date=args.date, team_id=args.team_id)
        carregar_stats_todos_jogadores(season=args.season)
        carregar_stats_todos_times(season=args.season)

if __name__ == "__main__":
    main()