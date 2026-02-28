from app.services import nba_api_client
from app.db.models import PlayerGameStats, Game, Player
from app.db.db_utils import get_db
from app.etl.func_normalize import _normalizar_string, _normalizar_inteiro

def carregar_stats_jogador(game_id):
    estatistica_jogador = nba_api_client.get_player_statistics(game_id=game_id)

    if not estatistica_jogador:
        return

    for db in get_db():
        jogo = db.query(Game).filter(Game.id == game_id).first()
        if not jogo:
            return

        season = jogo.season

        for item in estatistica_jogador:
            info_jogador = item.get("player")
            info_franquia = item.get("team")

            id_jogador = info_jogador.get("id") if isinstance(info_jogador, dict) else None
            id_franquia = info_franquia.get("id") if isinstance(info_franquia, dict) else None

            if not id_jogador or not id_franquia:
                continue

            jogador_existe_no_db = db.query(Player.id).filter(Player.id == id_jogador).first()
            if not jogador_existe_no_db:
                continue

            query_stats = db.query(PlayerGameStats).filter(PlayerGameStats.game_id == game_id, PlayerGameStats.player_id == id_jogador,
                                                           PlayerGameStats.team_id == id_franquia).first()

            if query_stats:
                continue

            nova_stats = PlayerGameStats(
                game_id=game_id,
                season=season,
                player_id=id_jogador,
                team_id=id_franquia,
                pos=_normalizar_string(item.get("pos")),
                minutes=_normalizar_string(item.get("min")),
                comment=_normalizar_string(item.get("comment")),
                points=_normalizar_inteiro(item.get("points")),
                fgm=_normalizar_inteiro(item.get("fgm")),
                fga=_normalizar_inteiro(item.get("fga")),
                fgp=_normalizar_string(item.get("fgp")),
                ftm=_normalizar_inteiro(item.get("ftm")),
                fta=_normalizar_inteiro(item.get("fta")),
                ftp=_normalizar_string(item.get("ftp")),
                tpm=_normalizar_inteiro(item.get("tpm")),
                tpa=_normalizar_inteiro(item.get("tpa")),
                tpp=_normalizar_string(item.get("tpp")),
                off_reb=_normalizar_inteiro(item.get("offReb")),
                def_reb=_normalizar_inteiro(item.get("defReb")),
                tot_reb=_normalizar_inteiro(item.get("totReb")),
                assists=_normalizar_inteiro(item.get("assists")),
                p_fouls=_normalizar_inteiro(item.get("pFouls")),
                steals=_normalizar_inteiro(item.get("steals")),
                turnovers=_normalizar_inteiro(item.get("turnovers")),
                blocks=_normalizar_inteiro(item.get("blocks")),
                plus_minus=_normalizar_string(item.get("plusMinus")),
            )
            db.add(nova_stats)

def carregar_stats_todos_jogadores(season, team_id=None):
    for db in get_db():
        consulta = db.query(Game).filter(Game.season == season)

        if team_id:
            consulta = consulta.filter((Game.home_team_id == team_id) | (Game.away_team_id == team_id))

        jogos = consulta.all()

        if not jogos:
            return

        for jogo in jogos:
            try:
                carregar_stats_jogador(game_id=jogo.id)
            except Exception:
                continue

if __name__ == "__main__":
    carregar_stats_todos_jogadores(season=2023)