import requests
from typing import Any, Dict, List, Optional

from app.config import config

class NBAAPIClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": self.base_url.replace("https://", "").replace("http://", "")
        }

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err} - Response: {response.text}")
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Connection error occurred: {conn_err}")
        except requests.exceptions.Timeout as timeout_err:
            print(f"Timeout error occurred: {timeout_err}")
        except requests.exceptions.RequestException as req_err:
            print(f"An unexpected error occurred: {req_err}")
        return None

    def get_seasons(self) -> Optional[List[int]]:
        response_data = self._make_request("seasons")
        if response_data and response_data.get("response"):
            return response_data["response"]
        return None

    def get_leagues(self) -> Optional[List[Dict[str, Any]]]:
        response_data = self._make_request("leagues")
        if response_data and response_data.get("response"):
            return response_data["response"]
        return None

    def get_teams(self, league_id: Optional[int] = None, season: Optional[int] = None) -> Optional[List[Dict[str, Any]]]:
        params = {}
        if league_id:
            params["league"] = league_id
        if season:
            params["season"] = season
        response_data = self._make_request("teams", params=params)
        if response_data and response_data.get("response"):
            return response_data["response"]
        return None

    def get_games(self, season: int, league_id: Optional[int] = None, date: Optional[str] = None, team_id: Optional[int] = None) -> Optional[List[Dict[str, Any]]]:
        params = {"season": season}
        if league_id:
            params["league"] = league_id
        if date:
            params["date"] = date
        if team_id:
            params["team"] = team_id
        response_data = self._make_request("games", params=params)
        if response_data and response_data.get("response"):
            return response_data["response"]
        return None

    def get_team_statistics(self, team_id: int, season: int, league_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        params = {"team": team_id, "season": season}
        if league_id:
            params["league"] = league_id
        response_data = self._make_request("teams/statistics", params=params)
        if response_data and response_data.get("response"):
            return response_data["response"]
        return None

    def get_players(self, team_id: Optional[int] = None, season: Optional[int] = None, player_id: Optional[int] = None) -> Optional[List[Dict[str, Any]]]:
        params = {}
        if team_id:
            params["team"] = team_id
        if season:
            params["season"] = season
        if player_id:
            params["id"] = player_id
        response_data = self._make_request("players", params=params)
        if response_data and response_data.get("response"):
            return response_data["response"]
        return None

    def get_player_statistics(self, game_id: int) -> Optional[List[Dict[str, Any]]]:
        params = {"game": game_id}
        response_data = self._make_request("players/statistics", params=params)
        if response_data and response_data.get("response"):
            return response_data["response"]
        return None

nba_api_client = NBAAPIClient(api_key=config.API_SPORTS_KEY, base_url=config.API_SPORTS_BASE_URL)