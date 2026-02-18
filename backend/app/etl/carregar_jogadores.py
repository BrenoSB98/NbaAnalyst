import logging
from datetime import datetime

from app.services import nba_api_client
from app.db.models import Player, PlayerTeamSeason
from app.db.db_utils import get_db

from app.etl.func_normalize import _normalizar_string, _normalizar_inteiro, _normalizar_decimal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def carregar_jogadores(team_id: int = None, season: int = None):
    logger.info(f"Iniciando carga de jogadores NBA (team_id={team_id}, season={season})...")    
    dados_jogadores = nba_api_client.get_players(team_id=team_id, season=season)
    
    if not dados_jogadores:
        logger.warning("Sem jogadores para carregar.")
        return
    
    total_original = len(dados_jogadores)
    jogadores_carregados = 0
    jogadores_existentes = 0
    jogadores_filtrados = 0
    jogadores_sem_id = 0
    temporadas_carregadas = 0
    temporadas_existentes = 0
    
    for db in get_db():
        for item in dados_jogadores:
            player_id = item.get("id")
            
            if not player_id:
                logger.warning(f"Dado de jogador sem ID. Pulando: {item}")
                jogadores_sem_id += 1
                continue
            
            dados_nba = item.get("nba", {})
            nba_start = _normalizar_inteiro(dados_nba.get("start"))
            
            if not nba_start or nba_start == 0:
                logger.debug(f"Jogador {player_id} ignorado: nba_start={nba_start}")
                jogadores_filtrados += 1
                continue
            
            firstname = _normalizar_string(item.get("firstname"))
            lastname = _normalizar_string(item.get("lastname"))
            
            if not firstname or not lastname:
                if firstname is None:
                    firstname = lastname
                elif lastname is None:
                    lastname = firstname
            
            jogador_existente = db.query(Player).filter(Player.id == player_id).first()
            
            if jogador_existente:
                jogadores_existentes += 1
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
                    data_nascimento_obj = datetime.strptime(
                        data_nascimento_str, "%Y-%m-%d"
                    ).date()
                except Exception as erro:
                    logger.warning(f"Data de nascimento inválida para jogador {player_id}: {data_nascimento_str}, erro: {erro}")
            
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
            jogadores_carregados += 1
            
            dados_ligas = item.get("leagues", {})
            if dados_ligas and season and team_id:
                liga_standard = dados_ligas.get("standard", {})
                numero_camisa = liga_standard.get("jersey")
                ativo = liga_standard.get("active", False)
                posicao = liga_standard.get("pos")
                codigo_liga = "standard"

                temporada_existente = db.query(PlayerTeamSeason).filter(
                    PlayerTeamSeason.player_id == player_id,
                    PlayerTeamSeason.team_id == team_id,
                    PlayerTeamSeason.season == season,
                    PlayerTeamSeason.league_code == codigo_liga
                ).first()
                
                if temporada_existente:
                    temporadas_existentes += 1
                    continue
                
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
                temporadas_carregadas += 1
    
    logger.info(
        f"Carga de jogadores NBA concluída. "
        f"{jogadores_carregados} jogadores carregados, {jogadores_existentes} já existiam, "
        f"{jogadores_filtrados} filtrados (não NBA), {jogadores_sem_id} sem ID. "
        f"{temporadas_carregadas} temporadas carregadas, {temporadas_existentes} já existiam."
    )
if __name__ == "__main__":
    carregar_jogadores()