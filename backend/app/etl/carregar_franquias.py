from app.services import nba_api_client
from app.db.models import Team, League, TeamLeagueInfo
from app.db.db_utils import get_db
from app.etl.func_normalize import _normalizar_inteiro, _normalizar_boolean, _normalizar_string

def carregar_times():
    dados_times = nba_api_client.get_teams()
    if not dados_times:
        return

    for db in get_db():
        for item in dados_times:
            team_id = _normalizar_inteiro(item.get("id"))
            team_name = _normalizar_string(item.get("name"))
            team_nickname = _normalizar_string(item.get("nickname"))
            team_code = _normalizar_string(item.get("code"))
            team_city = _normalizar_string(item.get("city"))
            team_logo = _normalizar_string(item.get("logo"))
            all_star = _normalizar_boolean(item.get("allStar", False))
            nba_franchise = _normalizar_boolean(item.get("nbaFranchise", False))

            if not team_id or not team_name:
                continue

            time_existente = db.query(Team).filter(Team.id == team_id).first()
            if time_existente:
                continue

            if not nba_franchise:
                continue

            novo_time = Team(
                id=team_id,
                name=team_name,
                nickname=team_nickname,
                code=team_code,
                city=team_city,
                logo=team_logo,
                all_star=all_star,
                nba_franchise=nba_franchise,
            )
            db.add(novo_time)

            leagues = item.get("leagues", {})
            if leagues:
                standard_league_info = leagues.get("standard", {}) or {}
                league_code = _normalizar_string(standard_league_info.get("code"))
                conference = _normalizar_string(standard_league_info.get("conference"))
                division = _normalizar_string(standard_league_info.get("division"))

                if league_code:
                    liga = db.query(League).filter(League.code == league_code).first()
                    if liga:
                        info_existente = db.query(TeamLeagueInfo).filter(TeamLeagueInfo.team_id == team_id, TeamLeagueInfo.league_id == liga.id).first()

                        if not info_existente:
                            team_league_info = TeamLeagueInfo(team_id=team_id, league_id=liga.id, conference=conference, division=division)
                            db.add(team_league_info)

if __name__ == "__main__":
    carregar_times()