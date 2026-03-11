import logging
import time
import requests

from app.config import config

logger = logging.getLogger(__name__)

TENTATIVAS_MAXIMAS = 3
ESPERA_RATE_LIMIT_SEGUNDOS = 15

def _fazer_requisicao(endpoint, params=None):
    url = f"{config.API_SPORTS_BASE_URL}/{endpoint}"
    cabecalhos = {
        "x-apisports-key": config.API_SPORTS_KEY
    }

    tentativa_atual = 1
    while tentativa_atual <= TENTATIVAS_MAXIMAS:
        try:
            resposta = requests.get(url, headers=cabecalhos, params=params, timeout=15)
            if resposta.status_code == 429:
                if tentativa_atual < TENTATIVAS_MAXIMAS:
                    logger.warning(f"Rate limit atingido (429) ao chamar '{endpoint}' —> tentativa {tentativa_atual}/{TENTATIVAS_MAXIMAS}. Aguardando {ESPERA_RATE_LIMIT_SEGUNDOS}s...")
                    time.sleep(ESPERA_RATE_LIMIT_SEGUNDOS)
                    tentativa_atual = tentativa_atual + 1
                    continue
                else:
                    logger.error(f"Rate limit atingido (429) ao chamar '{endpoint}' —> todas as {TENTATIVAS_MAXIMAS} tentativas esgotadas. Abortando.")
                    return None

            resposta.raise_for_status()
            dados = resposta.json()
            erros_api = dados.get("errors")
            if erros_api:
                logger.error(f"Erro retornado pela API-Sports em '{endpoint}': {erros_api}")
                return None

            if dados and dados.get("response") is not None:
                return dados["response"]

            return None

        except requests.exceptions.HTTPError as erro:
            logger.error(f"Erro HTTP ao chamar '{endpoint}': {erro}")
            return None

        except requests.exceptions.ConnectionError as erro:
            logger.error(f"Erro de conexão ao chamar '{endpoint}': {erro}")
            return None

        except requests.exceptions.Timeout as erro:
            logger.error(f"Timeout ao chamar '{endpoint}': {erro}")
            return None

        except requests.exceptions.RequestException as erro:
            logger.error(f"Erro ao chamar '{endpoint}': {erro}")
            return None
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