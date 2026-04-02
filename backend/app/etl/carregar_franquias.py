from app.services import nba_api_client
from app.db.models import Team, League, TeamLeagueInfo
from app.db.db_utils import get_db
from app.etl.func_normalize import _normalizar_inteiro, _normalizar_boolean, _normalizar_string
from app.core.logging_config import configurar_logger

logger = configurar_logger(__name__)

def carregar_times():
    logger.info("Buscando times...")
    dados_times = nba_api_client.get_teams()

    if not dados_times:
        logger.warning("API retornou vazio.")
        return

    logger.info(f"{len(dados_times)} times recebidos.")

    for db in get_db():
        total_inseridos = 0
        total_atualizados = 0
        total_sem_liga = 0
        total_ignorados = 0

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
                logger.info("Pulando — sem id/nome.")
                total_ignorados = total_ignorados + 1
                continue

            if not nba_franchise:
                logger.info(f"Pulando {team_name} — nao franquia.")
                total_ignorados = total_ignorados + 1
                continue

            if all_star:
                logger.info(f"Pulando {team_name} — all-star.")
                total_ignorados = total_ignorados + 1
                continue

            time_existente = db.query(Team).filter(Team.id == team_id).first()

            if time_existente:
                logger.info(f"Atualiza {team_name}.")
                time_existente.name = team_name
                time_existente.nickname = team_nickname
                time_existente.code = team_code
                time_existente.city = team_city
                time_existente.logo = team_logo
                time_existente.all_star = all_star if all_star is not None else False
                time_existente.nba_franchise = nba_franchise if nba_franchise is not None else False
                total_atualizados = total_atualizados + 1
            else:
                logger.info(f"Insere {team_name}.")
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

            leagues = item.get("leagues", {})
            logger.info(f"{team_name} — {len(leagues)} liga(s).")

            for nome_liga, dados_liga in leagues.items():
                if not isinstance(dados_liga, dict):
                    continue

                conference = _normalizar_string(dados_liga.get("conference"))
                division = _normalizar_string(dados_liga.get("division"))

                liga = db.query(League).filter(League.code == nome_liga).first()

                if not liga:
                    logger.warning(f"Liga '{nome_liga}' nao encontrada.")
                    total_sem_liga = total_sem_liga + 1
                    continue

                info_existente = db.query(TeamLeagueInfo).filter(TeamLeagueInfo.team_id == team_id, TeamLeagueInfo.league_id == liga.id).first()

                if info_existente:
                    logger.info(f"{team_name}/{nome_liga} — atualiza conf/div.")
                    if conference:
                        info_existente.conference = conference
                    if division:
                        info_existente.division = division
                else:
                    logger.info(f"{team_name}/{nome_liga} — vincula.")
                    nova_info = TeamLeagueInfo(team_id=team_id, league_id=liga.id, conference=conference, division=division)
                    db.add(nova_info)

        db.commit()
        logger.info("Commit ok.")

        if total_inseridos == 0 and total_atualizados == 0:
            logger.warning("Nenhum time salvo.")
        else:
            logger.info(f"Fim — ins={total_inseridos} atu={total_atualizados} ign={total_ignorados} sem_liga={total_sem_liga}")

if __name__ == "__main__":
    carregar_times()