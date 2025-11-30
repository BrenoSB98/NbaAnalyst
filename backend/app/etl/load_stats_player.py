import logging
from typing import Any, Optional

from app.services import nba_api_client
from app.db.models import PlayerGameStats, Game, Player
from app.db.db_utils import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
BAD_NULL_STRINGS = {"", "-", "--", "—", "N/A", "NA", "null", "NULL", " "}


def _normalize_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value in BAD_NULL_STRINGS:
            return None
    return value


def _normalize_int(value: Any) -> Optional[int]:
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


def _normalize_float(value: Any) -> Optional[float]:
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


def _normalize_bool(value: Any) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        value = value.strip().lower()
        if value in {"true", "1", "yes"}:
            return True
        if value in {"false", "0", "no"}:
            return False
    if isinstance(value, int):
        return bool(value)
    return None
   
def load_stats_player(game_id: int):
    logger.info("Iniciando carga de estatísticas de jogadores NBA")
    
    player_stats_data = nba_api_client.get_player_statistics(game_id=game_id)
    
    if player_stats_data:
        logger.info("API retornou %d registros de estatísticas para o jogo %s", len(player_stats_data), game_id)
    else:
        logger.warning("API retornou resposta vazia para o jogo %s", game_id)
        
    if not player_stats_data:
        logger.warning("Sem estatísticas de jogadores para carregar.")
        return
    stats_inserted = 0
    stats_skipped = 0
    stats_skipped_fk = 0
    
    with get_db() as db:
        for item in player_stats_data:
            player_info = item.get("player")
            team_info = item.get("team")            
            player_id = player_info.get("id") if isinstance(player_info, dict) else None
            team_id = team_info.get("id") if isinstance(team_info, dict) else None
            
            if not player_id or not team_id:
                logger.warning(f"Dado de jogo incompleto nas estatísticas do jogador: {item}. Pulando...")
                stats_skipped += 1
                continue
            
            player_exists = db.query(Player.id).filter(Player.id == player_id).first()
            if not player_exists:
                logger.warning(f"Ignorando estatística: player_id={player_id} do jogo {game_id} não existe na tabela players.")
                stats_skipped_fk += 1
                continue
                       
            query_stats = db.query(PlayerGameStats).filter(
                PlayerGameStats.game_id == game_id,
                PlayerGameStats.player_id == player_id,
                PlayerGameStats.team_id == team_id
            ).first()
            
            if query_stats:
                logger.info(f"Estatísticas do jogador {player_id} para o jogo {game_id} já existem. Pulando...")
                stats_skipped += 1
                continue
            
            pos = _normalize_str(item.get("pos"))
            minutes = _normalize_str(item.get("min"))
            comment = _normalize_str(item.get("comment"))
            
            points = _normalize_int(item.get("points"))
            fgm = _normalize_int(item.get("fgm"))
            fga = _normalize_int(item.get("fga"))
            fgp = _normalize_str(item.get("fgp"))
            ftm = _normalize_int(item.get("ftm"))
            fta = _normalize_int(item.get("fta"))
            ftp = _normalize_str(item.get("ftp"))
            tpm = _normalize_int(item.get("tpm"))
            tpa = _normalize_int(item.get("tpa"))
            tpp = _normalize_str(item.get("tpp"))
            offReb = _normalize_int(item.get("offReb"))
            defReb = _normalize_int(item.get("defReb"))
            totReb = _normalize_int(item.get("totReb"))
            assists = _normalize_int(item.get("assists"))
            pFouls = _normalize_int(item.get("pFouls"))
            steals = _normalize_int(item.get("steals"))
            turnovers = _normalize_int(item.get("turnovers"))
            blocks = _normalize_int(item.get("blocks"))
            plusMinus = _normalize_str(item.get("plusMinus"))
              
            new_stats = PlayerGameStats(
                game_id=game_id,
                player_id=player_id,
                team_id=team_id,
                pos=pos,
                minutes=minutes,
                comment=comment,
                points=points,
                fgm=fgm,
                fga=fga,
                fgp=fgp,
                ftm=ftm,
                fta=fta,
                ftp=ftp,
                tpm=tpm,
                tpa=tpa,
                tpp=tpp,
                off_reb=offReb,
                def_reb=defReb,
                tot_reb=totReb,
                assists=assists,
                p_fouls=pFouls,
                steals=steals,
                turnovers=turnovers,
                blocks=blocks,
                plus_minus=plusMinus
            )
            db.add(new_stats)
            stats_inserted += 1
    logger.info(f"Estatísticas do jogador {player_id} para o jogo {game_id} carregadas:{stats_inserted} inseridas, {stats_skipped} puladas, {stats_skipped_fk} puladas por FK.")

def load_stats_player_bulk(season: int, team_id: int = None):
    logger.info(f"Iniciando carga em massa de estatísticas de jogadores para a temporada {season}...")
    
    with get_db() as db:
        game_query = db.query(Game).filter(Game.season == season)
        if team_id:
            game_query = game_query.filter(
                (Game.home_team_id == team_id) | (Game.away_team_id == team_id)
            )
        game_ids = game_query.all()
        
        if not game_ids:
            logger.error("Sem jogos encontrados para carregar estatísticas de jogadores.")
            return
        
        for game_id in game_ids:
            try:
                load_stats_player(game_id=game_id.id)
            except Exception as e:
                logger.error(f"Erro ao carregar estatísticas para o jogo {game_id.id}: {e}")
                continue
    logger.info(f"Carga em massa de estatísticas de jogadores para a temporada {season} concluída.")

if __name__ == "__main__":
    load_stats_player_bulk()