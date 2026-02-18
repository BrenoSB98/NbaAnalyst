import logging

from app.services import nba_api_client
from app.db.models import Game, GameTeamScore, Team
from app.db.db_utils import get_db
from app.etl.func_normalize import _normalizar_string, _normalizar_inteiro, _processar_datetime


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def carregar_partidas(season: int, date: str = None, team_id: int = None):
    """
    Carrega partidas da NBA para uma temporada específica
    """
    logger.info(f"Iniciando partidas NBA para season={season}, date={date}, team_id={team_id}")
    dados_jogos = nba_api_client.get_games(season=season, date=date, team_id=team_id)

    if not dados_jogos:
        logger.warning(f"API sem partidas para season={season}, team_id={team_id}.")
        return

    total_jogos = len(dados_jogos)

    jogos_carregados = 0
    jogos_ignorados = 0
    jogos_invalidos = 0
    jogos_sem_times = 0

    for db in get_db():
        for item in dados_jogos:
            game_id = _normalizar_inteiro(item.get("id") or item.get("gameId"))

            if not game_id:
                logger.warning(f"Dado de jogo sem ID válido. Pulando: {item}")
                jogos_invalidos += 1
                continue

            jogo_existente = db.query(Game).filter(Game.id == game_id).first()
            if jogo_existente:
                jogos_ignorados += 1
                continue

            liga = _normalizar_string(item.get("league"))
            
            date_info = item.get("date", {}) or {}
            data_inicio = date_info.get("start")
            data_fim = date_info.get("end")
            duracao = _normalizar_string(date_info.get("duration"))
            
            estagio = _normalizar_string(item.get("stage"))

            status = item.get("status", {}) or {}
            status_curto = _normalizar_string(status.get("short"))
            status_longo = _normalizar_string(status.get("long"))

            periodos = item.get("periods", {}) or {}
            periodo_atual = _normalizar_inteiro(periodos.get("current"))
            total_periodos = _normalizar_inteiro(periodos.get("total"))
            fim_de_periodo = _normalizar_string(periodos.get("endOfPeriod"))

            arena = item.get("arena", {}) or {}
            nome_arena = _normalizar_string(arena.get("name"))
            cidade_arena = _normalizar_string(arena.get("city"))
            estado_arena = _normalizar_string(arena.get("state"))
            pais_arena = _normalizar_string(arena.get("country"))

            times = item.get("teams", {}) or {}
            info_time_casa = times.get("home", {}) or {}
            info_time_visitante = times.get("visitors", {}) or times.get("away", {}) or {}

            id_time_casa = _normalizar_inteiro(info_time_casa.get("id"))
            id_time_visitante = _normalizar_inteiro(info_time_visitante.get("id"))

            if not id_time_casa or not id_time_visitante:
                logger.warning(
                    f"Dado de time incompleto no jogo {game_id}: "
                    f"home={id_time_casa}, away={id_time_visitante}. Pulando..."
                )
                jogos_invalidos += 1
                continue
            
            time_casa_existe = db.query(Team.id).filter(Team.id == id_time_casa).first()
            time_visitante_existe = db.query(Team.id).filter(Team.id == id_time_visitante).first()
            if not time_casa_existe or not time_visitante_existe:
                logger.warning(
                    f"Ignorando jogo {game_id}: "
                    f"time casa {id_time_casa} ou time visitante {id_time_visitante} não existem na tabela teams."
                )
                jogos_sem_times += 1
                continue
            
            data_inicio_obj = _processar_datetime(data_inicio)
            data_fim_obj = _processar_datetime(data_fim)

            novo_jogo = Game(
                id=game_id,
                league=liga,
                season=season,
                date_start=data_inicio_obj,
                date_end=data_fim_obj,
                duration=duracao,
                stage=estagio,
                status_short=status_curto,
                status_long=status_longo,
                periods_current=periodo_atual,
                periods_total=total_periodos,
                periods_end_of_period=fim_de_periodo,
                arena_name=nome_arena,
                arena_city=cidade_arena,
                arena_state=estado_arena,
                arena_country=pais_arena,
                home_team_id=id_time_casa,
                away_team_id=id_time_visitante,
            )
            db.add(novo_jogo)
            jogos_carregados += 1

            placares = item.get("scores", {}) or {}
            placar_casa = placares.get("home", {}) or {}
            placar_visitante = placares.get("visitors", {}) or placares.get("away", {}) or {}

            linescore_casa = placar_casa.get("linescore", []) or []
            linescore_visitante = placar_visitante.get("linescore", []) or []

            serie_casa = placar_casa.get("series", {}) or {}
            serie_visitante = placar_visitante.get("series", {}) or {}

            placar_time_casa = GameTeamScore(
                game_id=game_id,
                team_id=id_time_casa,
                is_home=True,
                win=_normalizar_inteiro(placar_casa.get("win")),
                loss=_normalizar_inteiro(placar_casa.get("loss")),
                series_win=_normalizar_inteiro(serie_casa.get("win")),
                series_loss=_normalizar_inteiro(serie_casa.get("loss")),
                points=_normalizar_inteiro(placar_casa.get("points")),
                linescore_q1=_normalizar_inteiro(linescore_casa[0]) if len(linescore_casa) > 0 else None,
                linescore_q2=_normalizar_inteiro(linescore_casa[1]) if len(linescore_casa) > 1 else None,
                linescore_q3=_normalizar_inteiro(linescore_casa[2]) if len(linescore_casa) > 2 else None,
                linescore_q4=_normalizar_inteiro(linescore_casa[3]) if len(linescore_casa) > 3 else None,
            )
            db.add(placar_time_casa)

            placar_time_visitante = GameTeamScore(
                game_id=game_id,
                team_id=id_time_visitante,
                is_home=False,
                win=_normalizar_inteiro(placar_visitante.get("win")),
                loss=_normalizar_inteiro(placar_visitante.get("loss")),
                series_win=_normalizar_inteiro(serie_visitante.get("win")),
                series_loss=_normalizar_inteiro(serie_visitante.get("loss")),
                points=_normalizar_inteiro(placar_visitante.get("points")),
                linescore_q1=_normalizar_inteiro(linescore_visitante[0]) if len(linescore_visitante) > 0 else None,
                linescore_q2=_normalizar_inteiro(linescore_visitante[1]) if len(linescore_visitante) > 1 else None,
                linescore_q3=_normalizar_inteiro(linescore_visitante[2]) if len(linescore_visitante) > 2 else None,
                linescore_q4=_normalizar_inteiro(linescore_visitante[3]) if len(linescore_visitante) > 3 else None,
            )
            db.add(placar_time_visitante)

    logger.info(
        f"Carga de partidas NBA concluída. "
        f"{jogos_carregados} jogos carregados, {jogos_ignorados} já existiam, "
        f"{jogos_invalidos} inválidos/incompletos, {jogos_sem_times} pulados (times não cadastrados)."
    )

if __name__ == "__main__":
    carregar_partidas(season=2016)