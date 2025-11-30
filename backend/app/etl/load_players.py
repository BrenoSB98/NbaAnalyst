import logging
from datetime import datetime
from typing import Optional

from app.services import nba_api_client
from app.db.models import Player, PlayerTeamSeason
from app.db.db_utils import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BAD_NULL_STRINGS = {"", "-", "--", "—", "N/A", "NA", None, "null", "NULL"}

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

def load_players(team_id: int = None, season: int = None):
    logger.info("Iniciando carga de jogadores NBA")
    
    player_data = nba_api_client.get_players(team_id=team_id, season=season)
    
    if not player_data:
        logger.warning("Sem jogadores para carregar.")
        return
    
    with get_db() as db:
        for item in player_data:
            player_id = item.get("id")
            
            if not player_id:
                logger.warning(f"Dado de jogador incompleto: {item}. Pulando...")
                continue
            
            firstname = _normalize_str(item.get("firstname"))
            lastname = _normalize_str(item.get("lastname"))
            
            if not firstname or not lastname:
                if firstname is None:
                    firstname = lastname
                elif lastname is None:
                    lastname = firstname
            
            query_player = db.query(Player).filter(Player.id == player_id).first()
            
            if query_player:
                logger.info(f"Jogador {player_id} já existe. Pulando...")
                continue
            
            birth_data = item.get("birth", {})
            birth_date_str = birth_data.get("date")
            birth_country = _normalize_str(birth_data.get("country"))
            
            nba_data = item.get("nba", {})
            nba_start = _normalize_int(nba_data.get("start"))
            nba_pro = _normalize_int(nba_data.get("pro"))
            
            height_data = item.get("height", {})
            height_feet = _normalize_int(height_data.get("feets"))
            height_inches = _normalize_int(height_data.get("inches"))
            height_meters = _normalize_float(height_data.get("meters"))
            
            weight_data = item.get("weight", {})
            weight_pounds = _normalize_int(weight_data.get("pounds"))
            weight_kilograms = _normalize_float(weight_data.get("kilograms"))
            
            college = _normalize_str(item.get("college"))
            affiliation = _normalize_str(item.get("affiliation"))
            
            birth_date_ts = None
            if birth_date_str:
                try:
                    birth_date_ts = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
                except Exception as e:
                    logger.warning(f"Data de nascimento inválida para o jogador {player_id}: {birth_date_str}, erro: {e}")
            
            query_player = db.query(Player).filter(Player.id == player_id).first()
            
            if query_player:
                logger.info(f"Jogador {player_id} já existe. Pulando...")
                continue
            
            new_player = Player(
                id=player_id,
                firstname=firstname,
                lastname=lastname,
                birth_date=birth_date_ts,
                birth_country=birth_country,
                nba_start=nba_start,
                nba_pro=nba_pro,
                height_feet=height_feet,
                height_inches=height_inches,
                height_meters=height_meters,
                weight_pounds=weight_pounds,
                weight_kilograms=weight_kilograms,
                college=college,
                affiliation=affiliation
            )
            db.add(new_player)
            logger.info(f"Jogador {firstname} {lastname} ({player_id}) carregado com sucesso.")
            
            league_data = item.get("leagues", {})
            if league_data and season and team_id:
                standard_league = league_data.get("standard", {})
                jersey = standard_league.get("jersey")
                active = standard_league.get("active", False)
                pos = standard_league.get("pos")
                league_code = "standard"

                query_points = db.query(PlayerTeamSeason).filter(
                    PlayerTeamSeason.player_id == player_id,
                    PlayerTeamSeason.team_id == team_id,
                    PlayerTeamSeason.season == season,
                    PlayerTeamSeason.league_code == league_code
                ).first()
                
                if query_points:
                    logger.info(f"Temporada do jogador {player_id} para o time {team_id} na temporada {season} já existe. Pulando...")
                    continue
                
                player_team_season = PlayerTeamSeason(
                    player_id=player_id,
                    team_id=team_id,
                    season=season,
                    league_code=league_code,
                    jersey=jersey,
                    active=active,
                    pos=pos
                )
                db.add(player_team_season)
                logger.info(f"Temporada do jogador {player_id} para o time {team_id} na temporada {season} carregada com sucesso.")    
    logger.info("Carga de jogadores NBA concluída.")

if __name__ == "__main__":
    load_players()