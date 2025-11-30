import logging
from datetime import datetime
from typing import Optional, Any

from app.services import nba_api_client
from app.db.models import Game, GameTeamScore
from app.db.db_utils import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BAD_NULL_STRINGS = {"", "-", "--", "—", "N/A", "NA", None, "null", "NULL"}

def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            logger.warning("Formato de data/hora inválido recebido: %s", value)
            return None

def _normalize_str(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value in BAD_NULL_STRINGS:
            return None
    return value

def _normalize_int(value) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value in BAD_NULL_STRINGS:
            return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

def _normalize_float(value) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value in BAD_NULL_STRINGS:
            return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
       
def load_games(season: int, date: str = None, team_id: int = None):
    logger.info("Iniciando carga de jogos NBA")
    
    game_data = nba_api_client.get_games(season=season, date=date, team_id=team_id)
    
    if not game_data:
        logger.warning("Sem jogos para carregar.")
        return
    
    with get_db() as db:
        for item in game_data:
            game_id = item.get("id") or item.get("gameId")
            
            if not game_id:
                logger.warning(f"Dado de jogo incompleto: {item}. Pulando...")
                continue
            
            query_game = db.query(Game).filter(Game.id == game_id).first()            
            if query_game:
                logger.info(f"Jogo {game_id} já existe. Pulando...")
                continue
            
            league = _normalize_str(item.get("league"))
            date_start = item.get("date", {}).get("start")
            date_end = item.get("date", {}).get("end")
            duration = _normalize_str(item.get("date", {}).get("duration"))
            stage = _normalize_str(item.get("stage"))
            
            status = item.get("status")
            status_short = _normalize_str(status.get("short"))
            status_long = _normalize_str(status.get("long"))
            
            periods = item.get("periods",{})
            periods_current = _normalize_int(periods.get("current"))
            periods_total = _normalize_int(periods.get("total"))
            periods_end_of_period = _normalize_str(periods.get("endOfPeriod"))
            
            arena = item.get("arena", {})
            arena_name = _normalize_str(arena.get("name"))
            arena_city = _normalize_str(arena.get("city"))
            arena_state = _normalize_str(arena.get("state"))
            arena_country = _normalize_str(arena.get("country"))
            
            teams = item.get("teams", {})
            home_team_info = teams.get("home", {})
            visitors_team_info = teams.get("visitors", {})
            home_team_id = home_team_info.get("id")
            visitors_team_id = visitors_team_info.get("id")
            
            if not home_team_id or not visitors_team_id:
                logger.warning(f"Dado de time incompleto no jogo: {item}. Pulando...")
                continue
            
            date_start_ts = _parse_datetime(date_start)            
            date_end_ts = _parse_datetime(date_end)
            
            new_game = Game(
                id=game_id,
                league=league,
                season=season,
                date_start=date_start_ts,
                date_end=date_end_ts,
                duration=duration,
                stage=stage,
                status_short=status_short,
                status_long=status_long,
                periods_current=periods_current,
                periods_total=periods_total,
                periods_end_of_period=periods_end_of_period,
                arena_name=arena_name,
                arena_city=arena_city,
                arena_state=arena_state,
                arena_country=arena_country,
                home_team_id=home_team_id,
                away_team_id=visitors_team_id
            )
            db.add(new_game)
            logger.info(f"Jogo {game_id} carregado com sucesso.")
            
            scores = item.get("scores", {})
            home_score_info = scores.get("home", {})
            visitors_score_info = scores.get("visitors", {})
            
            home_line_score = home_score_info.get("line_score", []) or []
            away_line_score = visitors_score_info.get("line_score", []) or []
            
            home_series = home_score_info.get("series", {}) or {}
            away_series = visitors_score_info.get("series", {}) or {}
            
            home_game_score = GameTeamScore(
                game_id=game_id,
                team_id=home_team_id,
                is_home=True,
                win=_normalize_int(home_score_info.get("win")),
                loss=_normalize_int(home_score_info.get("loss")),
                series_win=_normalize_int(home_series.get("win")),
                series_loss=_normalize_int(home_series.get("loss")),
                points=_normalize_int(home_score_info.get("points")),
                linescore_q1=_normalize_int(home_line_score[0]) if len(home_line_score) > 0 else None,
                linescore_q2=_normalize_int(home_line_score[1]) if len(home_line_score) > 1 else None,
                linescore_q3=_normalize_int(home_line_score[2]) if len(home_line_score) > 2 else None,
                linescore_q4=_normalize_int(home_line_score[3]) if len(home_line_score) > 3 else None
            )
            db.add(home_game_score)
            logger.info(f"Placar do time da casa para o jogo {game_id} carregado com sucesso.")
            
            away_game_score = GameTeamScore(
                game_id=game_id,
                team_id=visitors_team_id,
                is_home=False,
                win=_normalize_int(visitors_score_info.get("win")),
                loss=_normalize_int(visitors_score_info.get("loss")),
                series_win=_normalize_int(away_series.get("win")),            
                series_loss=_normalize_int(away_series.get("loss")),
                points=_normalize_int(visitors_score_info.get("points")),
                linescore_q1=_normalize_int(away_line_score[0]) if len(away_line_score) > 0 else None,
                linescore_q2=_normalize_int(away_line_score[1]) if len(away_line_score) > 1 else None,
                linescore_q3=_normalize_int(away_line_score[2]) if len(away_line_score) > 2 else None,
                linescore_q4=_normalize_int(away_line_score[3]) if len(away_line_score) > 3 else None
            )
            db.add(away_game_score)
            logger.info(f"Placar do time visitante para o jogo {game_id} carregado com sucesso.")
    logger.info("Carga de jogos NBA concluída.")

if __name__ == "__main__":
    load_games()