import logging

from app.services import nba_api_client
from app.db.models import Team, League, TeamLeagueInfo
from app.db.db_utils import get_db

from app.etl.func_normalize import _normalizar_inteiro, _normalizar_boolean, _normalizar_string

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def carregar_times():
    """
    Carrega times da NBA a partir da API e insere no banco de dados.
    """
    logger.info("Iniciando carga de times NBA...")

    dados_times = nba_api_client.get_teams()
    if not dados_times:
        logger.warning("Sem times para carregar.")
        return

    times_carregados = 0
    times_existentes = 0
    times_nao_franquia = 0
    times_incompletos = 0
    infos_liga_carregadas = 0
    infos_liga_existentes = 0
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
                logger.warning(f"Dado de time incompleto: {item}. Pulando...")
                times_incompletos += 1
                continue

            time_existente = db.query(Team).filter(Team.id == team_id).first()
            if time_existente:
                times_existentes += 1
                continue
            
            if not nba_franchise:
                logger.debug(f"Time {team_name} ({team_id}) não é franquia NBA. Pulando...")
                times_nao_franquia += 1
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
            times_carregados += 1

            leagues = item.get("leagues", {})
            if leagues:
                standard_league_info = leagues.get("standard", {}) or {}
                league_code = _normalizar_string(standard_league_info.get("code"))
                conference = _normalizar_string(standard_league_info.get("conference"))
                division = _normalizar_string(standard_league_info.get("division"))

                if league_code:
                    liga = db.query(League).filter(League.code == league_code).first()
                    if liga:
                        info_existente = (db.query(TeamLeagueInfo).filter(
                            TeamLeagueInfo.team_id == team_id,
                            TeamLeagueInfo.league_id == liga.id,
                        ).first())

                        if not info_existente:
                            team_league_info = TeamLeagueInfo(
                                team_id=team_id,
                                league_id=liga.id,
                                conference=conference,
                                division=division,
                            )
                            db.add(team_league_info)
                            infos_liga_carregadas += 1
                        else:
                            infos_liga_existentes += 1

    logger.info(
        f"Carga de times NBA concluída. "
        f"{times_carregados} carregados, {times_existentes} já existiam, "
        f"{times_nao_franquia} não são franquias, {times_incompletos} incompletos. "
        f"{infos_liga_carregadas} informações de liga carregadas, {infos_liga_existentes} já existiam."
    )


if __name__ == "__main__":
    carregar_times()