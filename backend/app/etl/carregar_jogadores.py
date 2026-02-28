from datetime import datetime

from app.services import nba_api_client
from app.db.models import Player, PlayerTeamSeason
from app.db.db_utils import get_db
from app.etl.func_normalize import _normalizar_string, _normalizar_inteiro, _normalizar_decimal

def carregar_jogadores(team_id=None, season=None):
    dados_jogadores = nba_api_client.get_players(team_id=team_id, season=season)

    if not dados_jogadores:
        return

    for db in get_db():
        for item in dados_jogadores:
            player_id = item.get("id")

            if not player_id:
                continue

            dados_nba = item.get("nba", {})
            nba_start = _normalizar_inteiro(dados_nba.get("start"))

            if not nba_start or nba_start == 0:
                continue

            firstname = _normalizar_string(item.get("firstname"))
            lastname = _normalizar_string(item.get("lastname"))

            if not firstname and not lastname:
                continue
            if firstname is None:
                firstname = lastname
            if lastname is None:
                lastname = firstname

            jogador_existente = db.query(Player).filter(Player.id == player_id).first()
            if jogador_existente:
                continue

            dados_nascimento = item.get("birth", {})
            data_nascimento_str = dados_nascimento.get("date")
            pais_nascimento = _normalizar_string(dados_nascimento.get("country"))
            nba_pro = _normalizar_inteiro(dados_nba.get("pro"))

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
                    data_nascimento_obj = datetime.strptime(data_nascimento_str, "%Y-%m-%d").date()
                except Exception:
                    data_nascimento_obj = None

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
                affiliation=afiliacao
            )
            db.add(novo_jogador)

            dados_ligas = item.get("leagues", {})
            if dados_ligas and season and team_id:
                liga_standard = dados_ligas.get("standard", {})
                numero_camisa = liga_standard.get("jersey")
                ativo = liga_standard.get("active", False)
                posicao = liga_standard.get("pos")
                codigo_liga = "standard"

                temporada_existente = db.query(PlayerTeamSeason).filter(PlayerTeamSeason.player_id == player_id, PlayerTeamSeason.team_id == team_id,
                                                                        PlayerTeamSeason.season == season, PlayerTeamSeason.league_code == codigo_liga).first()

                if not temporada_existente:
                    temporada_jogador = PlayerTeamSeason(
                        player_id=player_id,
                        team_id=team_id,
                        season=season,
                        league_code=codigo_liga,
                        jersey=numero_camisa,
                        active=ativo,
                        pos=posicao
                    )
                    db.add(temporada_jogador)

if __name__ == "__main__":
    carregar_jogadores()