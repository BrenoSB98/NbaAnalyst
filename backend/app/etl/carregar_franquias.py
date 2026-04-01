import logging

from app.services import nba_api_client
from app.db.models import Team, League, TeamLeagueInfo
from app.db.db_utils import get_db
from app.etl.func_normalize import _normalizar_inteiro, _normalizar_boolean, _normalizar_string

logger = logging.getLogger(__name__)
_TERMOS_BUSCA_LIGA_NBA = ["NBA", "National Basketball Association", "standard"]

def _buscar_liga_nba_fallback(db):
    for termo in _TERMOS_BUSCA_LIGA_NBA:
        liga = db.query(League).filter(League.description.ilike(f"%{termo}%")).first()
        if liga:
            return liga
    liga = db.query(League).filter(League.code == "12").first()
    if liga:
        return liga
    return None

def carregar_times():
    dados_times = nba_api_client.get_teams()
    if not dados_times:
        logger.warning("Nenhum time retornado pela API.")
        return

    for db in get_db():
        total_inseridos  = 0
        total_atualizados = 0
        total_sem_liga   = 0

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
            if not nba_franchise:
                continue
            if all_star:
                continue

            time_existente = db.query(Team).filter(Team.id == team_id).first()
            if time_existente:
                time_existente.name = team_name
                time_existente.nickname = team_nickname
                time_existente.code = team_code
                time_existente.city  = team_city
                time_existente.logo = team_logo
                time_existente.all_star = all_star if all_star is not None else False
                time_existente.nba_franchise = nba_franchise if nba_franchise is not None else False
                total_atualizados = total_atualizados + 1
            else:
                novo_time = Team(
                    id=team_id,
                    name=team_name,
                    nickname=team_nickname,
                    code=team_code,
                    city=team_city,
                    logo=team_logo,
                    all_star=all_star if all_star is not None else False,
                    nba_franchise=nba_franchise if nba_franchise is not None else False,
                )
                db.add(novo_time)
                total_inseridos = total_inseridos + 1

            leagues       = item.get("leagues", {})
            standard_info = leagues.get("standard", {})
            league_id_api = _normalizar_inteiro(standard_info.get("id"))
            conference    = _normalizar_string(standard_info.get("conference"))
            division      = _normalizar_string(standard_info.get("division"))

            liga = None

            if league_id_api is not None:
                liga = db.query(League).filter(League.code == str(league_id_api)).first()

            if not liga:
                league_code_str = _normalizar_string(standard_info.get("code"))
                if league_code_str:
                    liga = db.query(League).filter(League.code == league_code_str).first()

            if not liga:
                liga = _buscar_liga_nba_fallback(db)

                if liga:
                    logger.warning(f"Time {team_id} ({team_name}) —> campo league ausente na API. Liga encontrada via fallback: code='{liga.code}'.")
                else:
                    logger.warning(f"Time {team_id} ({team_name}) —> campo league ausente e liga NBA nao encontrada no banco. TeamLeagueInfo nao sera salvo.")
                    total_sem_liga = total_sem_liga + 1
                    continue

            info_existente = db.query(TeamLeagueInfo).filter(
                TeamLeagueInfo.team_id   == team_id,
                TeamLeagueInfo.league_id == liga.id
            ).first()

            if info_existente:
                if conference:
                    info_existente.conference = conference
                if division:
                    info_existente.division = division
            else:
                nova_info = TeamLeagueInfo(
                    team_id=team_id,
                    league_id=liga.id,
                    conference=conference,
                    division=division,
                )
                db.add(nova_info)

        db.commit()

        if total_inseridos == 0 and total_atualizados == 0:
            logger.warning("Nenhum time inserido ou atualizado.")
        else:
            logger.warning(f"Franquias carregadas —> inseridos={total_inseridos}, atualizados={total_atualizados}, sem_liga={total_sem_liga}")


if __name__ == "__main__":
    carregar_times()