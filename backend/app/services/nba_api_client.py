import logging
import requests

from app.config import config

logger = logging.getLogger(__name__)

def _fazer_requisicao(endpoint, params=None):
    url = f"{config.API_SPORTS_BASE_URL}/{endpoint}"
    cabecalhos = {
        "x-rapidapi-key": config.API_SPORTS_KEY,
        "x-rapidapi-host": config.API_SPORTS_BASE_URL.replace("https://", "").replace("http://", "")
    }

    try:
        resposta = requests.get(url, headers=cabecalhos, params=params, timeout=10)
        resposta.raise_for_status()
        dados = resposta.json()
        if dados and dados.get("response"):
            return dados["response"]
        return None
    except requests.exceptions.HTTPError as erro:
        logger.error(f"Erro HTTP ao chamar {endpoint}: {erro}")
        return None
    except requests.exceptions.ConnectionError as erro:
        logger.error(f"Erro de conexão ao chamar {endpoint}: {erro}")
        return None
    except requests.exceptions.Timeout as erro:
        logger.error(f"Timeout ao chamar {endpoint}: {erro}")
        return None
    except requests.exceptions.RequestException as erro:
        logger.error(f"Erro inesperado ao chamar {endpoint}: {erro}")
        return None

def get_seasons():
    return _fazer_requisicao("seasons")

def get_leagues():
    return _fazer_requisicao("leagues")

def get_teams(league_id=None, season=None):
    params = {}
    if league_id:
        params["league"] = league_id
    if season:
        params["season"] = season
    return _fazer_requisicao("teams", params=params)

def get_games(season, league_id=None, date=None, team_id=None):
    params = {"season": season}
    if league_id:
        params["league"] = league_id
    if date:
        params["date"] = date
    if team_id:
        params["team"] = team_id
    return _fazer_requisicao("games", params=params)

def get_team_statistics(team_id, season, league_id=None):
    params = {"team": team_id, "season": season}
    if league_id:
        params["league"] = league_id
    return _fazer_requisicao("teams/statistics", params=params)

def get_players(team_id=None, season=None, player_id=None):
    params = {}
    if team_id:
        params["team"] = team_id
    if season:
        params["season"] = season
    if player_id:
        params["id"] = player_id
    return _fazer_requisicao("players", params=params)

def get_player_statistics(game_id):
    params = {"game": game_id}
    return _fazer_requisicao("players/statistics", params=params)

def get_game_statistics(game_id):
    params = {"id": game_id}
    return _fazer_requisicao("games/statistics", params=params)