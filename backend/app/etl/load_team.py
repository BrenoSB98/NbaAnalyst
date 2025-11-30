import logging

from app.services import nba_api_client
from app.db.models import Team, League, TeamLeagueInfo
from app.db.db_utils import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

    
def load_teams():
    logger.info("Iniciando carga de times NBA...")
    
    team_data = nba_api_client.get_teams()
    if not team_data:
        logger.warning("Sem times para carregar.")
        return
    
    with get_db() as db:
        for item in team_data:
            team_id = item.get("id")
            team_name = item.get("name")
            team_nickname = item.get("nickname")
            team_code = item.get("code")
            team_city = item.get("city")
            team_logo = item.get("logo")
            all_star = item.get("all_star", False)
            nba_franchise = item.get("nba_franchise", False)
            
            if not team_id or not team_name:
                logger.warning(f"Dado de time incompleto: {item}. Pulando...")
                continue
            
            query_team = db.query(Team).filter(Team.id == team_id).first()
            if query_team:
                logger.info(f"Time {team_name} ({team_id}) já existe. Pulando...")
                continue
            new_team = Team(
                id=team_id,
                name=team_name,
                nickname=team_nickname,
                code=team_code,
                city=team_city,
                logo=team_logo,
                all_star=all_star,
                nba_franchise=nba_franchise
            )
            db.add(new_team)
            logger.info(f"Time {team_name} ({team_id}) carregado com sucesso.")
            
            leagues = item.get("leagues", {})
            if leagues:
                standard_league_name = leagues.get("standard", {})
                league_code = standard_league_name.get("code")
                conference = standard_league_name.get("conference")
                division = standard_league_name.get("division")
                
                if league_code:
                    query_league = db.query(League).filter(League.code == league_code).first()
                    if query_league:
                        new_query = db.query(TeamLeagueInfo).filter(
                            TeamLeagueInfo.team_id == team_id,
                            TeamLeagueInfo.league_id == query_league.id
                        ).first()
                        
                        if not new_query:
                            team_league_info = TeamLeagueInfo(
                                team_id=team_id,
                                league_id=query_league.id,
                                conference=conference,
                                division=division
                            )
                            db.add(team_league_info)
                            logger.info(f"Informações da liga para o time {team_name} adicionadas com sucesso.")
                        else:
                            logger.info(f"Informações da liga para o time {team_name} já existem. Pulando...")
    logger.info("Carga de times NBA concluída.")

if __name__ == "__main__":
    load_teams()