from datetime import datetime

from app.core.logging_config import configurar_logger
from app.db.db_utils import get_db
from app.db.models import Player, PlayerTeamSeason
from app.etl.func_normalize import (
    _normalizar_decimal,
    _normalizar_inteiro,
    _normalizar_string,
    normalizar_posicao, # type: ignore
)
from app.services import nba_api_client
from sqlalchemy import select

logger = configurar_logger(__name__)


def carregar_jogadores(team_id=None, season=None):
    logger.info(f"Buscando jogadores: time={team_id} temp={season}...")
    dados_jogadores = nba_api_client.get_players(team_id=team_id, season=season)

    if not dados_jogadores:
        logger.warning(f"API retornou vazio: time={team_id} temp={season}.")
        return

    logger.info(f"{len(dados_jogadores)} jogadores recebidos.")

    for db in get_db():
        total_inseridos = 0
        total_atualizados = 0

        for item in dados_jogadores:
            player_id = _normalizar_inteiro(item.get("id"))
            if not player_id:
                continue

            firstname = _normalizar_string(item.get("firstname"))
            lastname = _normalizar_string(item.get("lastname"))
            if not firstname and not lastname:
                continue

            if firstname is None:
                firstname = lastname
            if lastname is None:
                lastname = firstname

            dados_nba = item.get("nba", {})
            nba_start = _normalizar_inteiro(dados_nba.get("start"))
            nba_pro = _normalizar_inteiro(dados_nba.get("pro"))

            dados_nascimento = item.get("birth", {})
            data_nascimento_str = dados_nascimento.get("date")
            pais_nascimento = _normalizar_string(dados_nascimento.get("country"))

            dados_altura = item.get("height", {})
            altura_pes = _normalizar_inteiro(dados_altura.get("feets"))
            altura_polegadas = _normalizar_inteiro(dados_altura.get("inches"))
            altura_metros = _normalizar_decimal(dados_altura.get("meters"))

            dados_peso = item.get("weight", {})
            peso_libras = _normalizar_inteiro(dados_peso.get("pounds"))
            peso_quilos = _normalizar_decimal(dados_peso.get("kilograms"))

            faculdade = _normalizar_string(item.get("college"))
            afiliacao = _normalizar_string(item.get("affiliation"))

            data_nascimento_obj = None
            if data_nascimento_str:
                try:
                    data_nascimento_obj = datetime.strptime(
                        data_nascimento_str, "%Y-%m-%d"
                    ).date()
                except Exception:
                    data_nascimento_obj = None

            dados_ligas_pos = item.get("leagues", {})
            liga_standard_pos = dados_ligas_pos.get("standard", {})
            posicao_crua = _normalizar_string(liga_standard_pos.get("pos"))
            posicao_normalizada = normalizar_posicao(posicao_crua)

            jogador_existente = db.execute(
                select(Player).where(Player.id == player_id)
            ).scalar_one_or_none()
            if jogador_existente:
                logger.info(f"Atualiza jogador {player_id}.")
                jogador_existente.firstname = firstname # type: ignore
                jogador_existente.lastname = lastname # type: ignore
                jogador_existente.birth_date = data_nascimento_obj # type: ignore
                jogador_existente.birth_country = pais_nascimento # type: ignore
                jogador_existente.nba_start = nba_start # type: ignore
                jogador_existente.nba_pro = nba_pro # type: ignore
                jogador_existente.height_feet = altura_pes # type: ignore
                jogador_existente.height_inches = altura_polegadas # type: ignore
                jogador_existente.height_meters = altura_metros # type: ignore
                jogador_existente.weight_pounds = peso_libras # type: ignore
                jogador_existente.weight_kilograms = peso_quilos # type: ignore
                jogador_existente.college = faculdade # type: ignore
                jogador_existente.affiliation = afiliacao # type: ignore
                if not jogador_existente.pos and posicao_normalizada: # type: ignore
                    jogador_existente.pos = posicao_normalizada # type: ignore
                total_atualizados = total_atualizados + 1
            else:
                logger.info(f"Insere jogador {player_id}: {firstname} {lastname}.")
                novo_jogador = Player(
                    id=player_id,
                    firstname=firstname,
                    lastname=lastname,
                    birth_date=data_nascimento_obj,
                    birth_country=pais_nascimento,
                    nba_start=nba_start,
                    nba_pro=nba_pro,
                    height_feet=altura_pes,
                    height_inches=altura_polegadas,
                    height_meters=altura_metros,
                    weight_pounds=peso_libras,
                    weight_kilograms=peso_quilos,
                    college=faculdade,
                    affiliation=afiliacao,
                    pos=posicao_normalizada,
                )
                db.add(novo_jogador)
                total_inseridos = total_inseridos + 1

            if not season or not team_id:
                continue

            dados_ligas = item.get("leagues", {})
            liga_standard = dados_ligas.get("standard", {})
            numero_camisa = _normalizar_inteiro(liga_standard.get("jersey"))
            ativo = liga_standard.get("active", False)
            posicao = _normalizar_string(liga_standard.get("pos"))
            codigo_liga = "standard"

            vinculo_existente = db.execute(
                select(PlayerTeamSeason).where(
                    PlayerTeamSeason.player_id == player_id,
                    PlayerTeamSeason.team_id == team_id,
                    PlayerTeamSeason.season == season,
                    PlayerTeamSeason.league_code == codigo_liga,
                )
            ).scalar_one_or_none()

            if vinculo_existente:
                logger.info(f"Atualiza vinculo {player_id}/time={team_id}.")
                vinculo_existente.jersey = numero_camisa # type: ignore
                if isinstance(ativo, bool):
                    vinculo_existente.active = ativo # type: ignore
                else:
                    vinculo_existente.active = bool(ativo) # type: ignore
                vinculo_existente.pos = posicao # type: ignore
            else:
                logger.info(f"Vincula {player_id}/time={team_id}/temp={season}.")
                novo_vinculo = PlayerTeamSeason(
                    player_id=player_id,
                    team_id=team_id,
                    season=season,
                    league_code=codigo_liga,
                    jersey=numero_camisa,
                    active=ativo if isinstance(ativo, bool) else bool(ativo),
                    pos=posicao,
                )
                db.add(novo_vinculo)

        db.commit()
        logger.info("Commit ok.")

        if total_inseridos == 0 and total_atualizados == 0:
            logger.warning(f"Nenhum jogador salvo: time={team_id} temp={season}.")
        else:
            logger.info(f"Fim: ins={total_inseridos} atu={total_atualizados}")


if __name__ == "__main__":
    carregar_jogadores()
