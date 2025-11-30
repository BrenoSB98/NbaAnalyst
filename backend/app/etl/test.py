from app.services import nba_api_client

data = nba_api_client.get_players(team_id=1, season=2023)
print(type(data), len(data) if data else data)
if data:
    from pprint import pprint
    pprint(data[0])