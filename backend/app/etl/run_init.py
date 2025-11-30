import argparse
import logging

from app.etl.load_league import load_league
from app.etl.load_season import load_season
from app.etl.load_team import load_teams
from app.etl.load_players import load_players
from app.etl.load_team_players import load_team_players
from app.etl.load_games import load_games
from app.etl.load_stats_player import load_stats_player, load_stats_player_bulk

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
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
            "season",
            "league",
            "teams",
            "players",
            "players_teams",
            "games",
            "stats_player",
            "stats_player_bulk",
            "all"],
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
    
    if args.load == "season":
        load_season()
    elif args.load == "league":
        load_league()
    elif args.load == "teams":
        load_teams()
    elif args.load == "players":
        if not args.season and not args.team_id:
            logger.error("Para carregar jogadores, tanto 'season' quanto 'team_id' devem ser fornecidos.")
            return
        load_players(team_id=args.team_id, season=args.season)
    elif args.load == "players_teams":
        if not args.season:
            logger.error("Para carregar jogadores por time, 'season' deve ser fornecido.")
            return
        load_team_players(season=args.season)
    elif args.load == "games":
        if not args.season:
            logger.error("Para carregar games é necessário informar --season.")
            return
        load_games(season=args.season, date=args.date, team_id=args.team_id)
    elif args.load == "stats_player":
        if not args.game_id:
            logger.error("Para carregar stats_player é necessário informar --game_id.")
            return
        load_stats_player(game_id=args.game_id)

    elif args.load == "stats_player_bulk":
        if not args.season:
            logger.error("Para carregar stats_player_bulk é necessário informar --season.")
            return
        load_stats_player_bulk(season=args.season, team_id=args.team_id)
    elif args.load == "all":
        load_season()
        load_league()
        load_teams()
        load_team_players(season=args.season)
        load_games(season=args.season, date=args.date, team_id=args.team_id)
        load_stats_player_bulk(season=args.season)
        
if __name__ == "__main__":
    main()
    