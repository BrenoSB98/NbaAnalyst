from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from app.db.models import Player, Team, Game, PlayerGameStats, GameTeamScore
from datetime import datetime, timedelta
import numpy as np
from app.db.db_utils import get_db

def converter_para_int(valor):
    if valor is None:
        return 0
    if isinstance(valor, str):
        if valor == "":
            return 0
        return int(valor)
    return valor


def converter_para_float(valor):
    if valor is None:
        return 0.0
    if isinstance(valor, str):
        if valor == "":
            return 0.0
        return float(valor)
    return valor


def calcular_totais_e_medias(stats_data):
    if len(stats_data) == 0:
        return None

    total_points = 0
    total_assists = 0
    total_rebounds = 0
    total_steals = 0
    total_blocks = 0
    total_turnovers = 0
    total_minutes = 0
    total_fgm = 0
    total_fga = 0
    total_tpm = 0
    total_tpa = 0
    total_ftm = 0
    total_fta = 0
    total_off_reb = 0
    total_def_reb = 0
    total_fouls = 0
    total_plus_minus = 0

    lista_jogos = []

    for stat_data in stats_data:
        stat = stat_data[0]
        jogo = stat_data[1]

        total_points = total_points + converter_para_int(stat.points)
        total_assists = total_assists + converter_para_int(stat.assists)
        total_rebounds = total_rebounds + converter_para_int(stat.tot_reb)
        total_steals = total_steals + converter_para_int(stat.steals)
        total_blocks = total_blocks + converter_para_int(stat.blocks)
        total_turnovers = total_turnovers + converter_para_int(stat.turnovers)
        total_minutes = total_minutes + converter_para_int(stat.minutes)
        total_fgm = total_fgm + converter_para_int(stat.fgm)
        total_fga = total_fga + converter_para_int(stat.fga)
        total_tpm = total_tpm + converter_para_int(stat.tpm)
        total_tpa = total_tpa + converter_para_int(stat.tpa)
        total_ftm = total_ftm + converter_para_int(stat.ftm)
        total_fta = total_fta + converter_para_int(stat.fta)
        total_off_reb = total_off_reb + converter_para_int(stat.off_reb)
        total_def_reb = total_def_reb + converter_para_int(stat.def_reb)
        total_fouls = total_fouls + converter_para_int(stat.p_fouls)
        total_plus_minus = total_plus_minus + converter_para_int(stat.plus_minus)

        jogo_info = {
            "game_id": jogo.id,
            "date": jogo.date_start,
            "points": converter_para_int(stat.points),
            "assists": converter_para_int(stat.assists),
            "rebounds": converter_para_int(stat.tot_reb)
        }
        lista_jogos.append(jogo_info)

    num_jogos = len(stats_data)

    media_points = round(total_points / num_jogos, 2)
    media_assists = round(total_assists / num_jogos, 2)
    media_rebounds = round(total_rebounds / num_jogos, 2)
    media_steals = round(total_steals / num_jogos, 2)
    media_blocks = round(total_blocks / num_jogos, 2)
    media_turnovers = round(total_turnovers / num_jogos, 2)
    media_minutes = round(total_minutes / num_jogos, 2)
    media_off_reb = round(total_off_reb / num_jogos, 2)
    media_def_reb = round(total_def_reb / num_jogos, 2)
    media_fouls = round(total_fouls / num_jogos, 2)
    media_plus_minus = round(total_plus_minus / num_jogos, 2)

    fg_pct = 0
    if total_fga > 0:
        fg_pct = round((total_fgm / total_fga) * 100, 2)
    three_pct = 0
    if total_tpa > 0:
        three_pct = round((total_tpm / total_tpa) * 100, 2)
    ft_pct = 0
    if total_fta > 0:
        ft_pct = round((total_ftm / total_fta) * 100, 2)

    resultado = {
        "num_jogos": num_jogos,
        "averages": {
            "points": media_points,
            "assists": media_assists,
            "rebounds": media_rebounds,
            "off_rebounds": media_off_reb,
            "def_rebounds": media_def_reb,
            "steals": media_steals,
            "blocks": media_blocks,
            "turnovers": media_turnovers,
            "fouls": media_fouls,
            "minutes": media_minutes,
            "plus_minus": media_plus_minus,
            "fg_pct": fg_pct,
            "three_pct": three_pct,
            "ft_pct": ft_pct
        },
        "totals": {
            "points": total_points,
            "assists": total_assists,
            "rebounds": total_rebounds,
            "off_rebounds": total_off_reb,
            "def_rebounds": total_def_reb,
            "steals": total_steals,
            "blocks": total_blocks,
            "turnovers": total_turnovers,
            "fouls": total_fouls,
            "fgm": total_fgm,
            "fga": total_fga,
            "tpm": total_tpm,
            "tpa": total_tpa,
            "ftm": total_ftm,
            "fta": total_fta
        },
        "games": lista_jogos
    }

    return resultado

def buscar_top_jogadores_por_stat(db, season, stat_field, stat_label, limit):
    resultados = (
        db.query(
            PlayerGameStats.player_id,
            func.sum(stat_field).label(stat_label),
            func.count(PlayerGameStats.game_id).label("games_played")
        )
        .join(Game, PlayerGameStats.game_id == Game.id)
        .filter(Game.season == season, Game.status_short == 3)
        .group_by(PlayerGameStats.player_id)
        .order_by(desc(stat_label))
        .limit(limit)
        .all()
    )

    lista_top = []
    for resultado in resultados:
        player_id = resultado[0]
        total_stat = converter_para_int(resultado[1])
        games_played = resultado[2]

        jogador = db.query(Player).filter(Player.id == player_id).first()
        if jogador:
            nome_completo = f"{jogador.firstname} {jogador.lastname}"
        else:
            nome_completo = "Desconhecido"

        media = 0
        if games_played > 0:
            media = round(total_stat / games_played, 2)

        item = {
            "player_id": player_id,
            "player_name": nome_completo,
            f"total_{stat_label}": total_stat,
            "games_played": games_played,
            "avg": media
        }
        lista_top.append(item)
    return lista_top

def calcular_medias_ultimos_n_jogos(db, player_id, n_games, season=None):
    query = (
        db.query(PlayerGameStats, Game)
        .join(Game, PlayerGameStats.game_id == Game.id)
        .filter(PlayerGameStats.player_id == player_id, Game.status_short == 3)
    )

    if season:
        query = query.filter(Game.season == season)
    stats = query.order_by(Game.date_start.desc()).limit(n_games).all()
    resultado = calcular_totais_e_medias(stats)

    if resultado:
        resultado["games_analyzed"] = resultado.pop("num_jogos")
    return resultado

def calcular_medias_casa_fora(db, player_id, season, location):
    if location == "home":
        buscar_home = True
    else:
        buscar_home = False

    stats_query = (
        db.query(PlayerGameStats, Game, GameTeamScore)
        .join(Game, PlayerGameStats.game_id == Game.id)
        .join(GameTeamScore, and_(GameTeamScore.game_id == Game.id, GameTeamScore.team_id == PlayerGameStats.team_id))
        .filter(
            PlayerGameStats.player_id == player_id,
            Game.season == season,
            Game.status_short == 3,
            GameTeamScore.is_home == buscar_home
        )
        .all()
    )

    stats_formatadas = []
    for item in stats_query:
        stats_formatadas.append((item[0], item[1]))

    resultado = calcular_totais_e_medias(stats_formatadas)
    if resultado:
        resultado["games_played"] = resultado.pop("num_jogos")
    return resultado

def calcular_medias_temporada_completa(db, player_id, season):
    stats_query = (
        db.query(PlayerGameStats, Game)
        .join(Game, PlayerGameStats.game_id == Game.id)
        .filter(PlayerGameStats.player_id == player_id, Game.season == season, Game.status_short == 3)
        .all()
    )

    resultado = calcular_totais_e_medias(stats_query)
    if resultado:
        resultado["games_played"] = resultado.pop("num_jogos")
    return resultado

def calcular_medias_contra_time(db, player_id, opponent_team_id, season=None):
    query = (
        db.query(PlayerGameStats, Game)
        .join(Game, PlayerGameStats.game_id == Game.id)
        .filter(PlayerGameStats.player_id == player_id, Game.status_short == 3)
    )

    if season:
        query = query.filter(Game.season == season)

    stats_all = query.all()
    stats_filtradas = []
    for stat_data in stats_all:
        stat = stat_data[0]
        jogo = stat_data[1]

        time_jogador = stat.team_id
        if jogo.home_team_id == time_jogador:
            adversario = jogo.away_team_id
        else:
            adversario = jogo.home_team_id

        if adversario == opponent_team_id:
            stats_filtradas.append(stat_data)

    resultado = calcular_totais_e_medias(stats_filtradas)
    if resultado:
        resultado["games_played"] = resultado.pop("num_jogos")
    return resultado

def calcular_medias_ultimos_dias(db, player_id, days, season=None):
    data_limite = datetime.now() - timedelta(days=days)

    query = (
        db.query(PlayerGameStats, Game)
        .join(Game, PlayerGameStats.game_id == Game.id)
        .filter(PlayerGameStats.player_id == player_id, Game.status_short == 3, Game.date_start >= data_limite)
    )

    if season:
        query = query.filter(Game.season == season)

    stats = query.order_by(Game.date_start.desc()).all()
    resultado = calcular_totais_e_medias(stats)
    if resultado:
        resultado["games_analyzed"] = resultado.pop("num_jogos")
        resultado["days"] = days
    return resultado

def calcular_defesa_adversaria_stat(db: Session, team_id: int, season: int, stat_name: str = "points"):
    stats_sofridas = (db.query(PlayerGameStats).join(Game, PlayerGameStats.game_id == Game.id)
                      .filter(Game.season == season, Game.status_short == 3, PlayerGameStats.team_id != team_id,
                              ((Game.home_team_id == team_id) | (Game.away_team_id == team_id))).all()
                      )
    if not stats_sofridas:
        return 0.0

    total_stat = sum(float(getattr(s, stat_name, 0) or 0) for s in stats_sofridas)
    num_jogos = db.query(Game).filter(Game.season == season, Game.status_short == 3, ((Game.home_team_id == team_id) | (Game.away_team_id == team_id))).count()
    return round(total_stat / num_jogos, 2) if num_jogos > 0 else 0.0

def calcular_metricas_consistencia(db: Session, player_id: int, season: int, stat_name: str = "points"):
    stats = (db.query(getattr(PlayerGameStats, stat_name)).join(Game, PlayerGameStats.game_id == Game.id)
             .filter(PlayerGameStats.player_id == player_id, Game.season == season).all()
             )
    
    valores = [float(v[0] or 0) for v in stats]
    if not valores:
        return None

    return {
        "media": round(np.mean(valores), 2),
        "desvio_padrao": round(np.std(valores), 2),
        "max": max(valores),
        "min": min(valores),
        "cv": round(np.std(valores) / np.mean(valores), 2) if np.mean(valores) > 0 else 0 # Coeficiente de Variação
    }

def calcular_dias_descanso(db: Session, player_id: int, game_date, season: int):
    jogo_anterior = (db.query(Game).join(PlayerGameStats, PlayerGameStats.game_id == Game.id)
                     .filter(PlayerGameStats.player_id == player_id, Game.season == season, Game.status_short == 3, Game.date_start < game_date)
                     .order_by(Game.date_start.desc()).first()
                     )    
    if not jogo_anterior:
        return 3
    
    delta = game_date - jogo_anterior.date_start
    return min(delta.days, 7)
  
def buscar_top_pontuadores(db, season, limit=10):
    return buscar_top_jogadores_por_stat(db=db, season=season, stat_field=PlayerGameStats.points, stat_label="points", limit=limit)

def buscar_top_assistencias(db, season, limit=10):
    return buscar_top_jogadores_por_stat(db=db, season=season, stat_field=PlayerGameStats.assists, stat_label="assists", limit=limit)

def buscar_top_rebotes(db, season, limit=10):
    return buscar_top_jogadores_por_stat(db=db, season=season, stat_field=PlayerGameStats.tot_reb, stat_label="rebounds", limit=limit)

def buscar_top_roubos_bola(db, season, limit=10):
    return buscar_top_jogadores_por_stat(db=db, season=season, stat_field=PlayerGameStats.steals, stat_label="steals", limit=limit)

def buscar_top_bloqueios(db, season, limit=10):
    return buscar_top_jogadores_por_stat(db=db, season=season, stat_field=PlayerGameStats.blocks, stat_label="blocks", limit=limit)

def buscar_top_turnovers(db, season, limit=10):
    return buscar_top_jogadores_por_stat(db=db, season=season, stat_field=PlayerGameStats.turnovers, stat_label="turnovers", limit=limit)

def buscar_top_arremessos_campo(db, season, limit=10):
    return buscar_top_jogadores_por_stat(db=db, season=season, stat_field=PlayerGameStats.fgm, stat_label="field_goals_made", limit=limit)

def buscar_top_arremessos_tres(db, season, limit=10):
    return buscar_top_jogadores_por_stat(db=db, season=season, stat_field=PlayerGameStats.tpm, stat_label="three_points_made", limit=limit)

def buscar_top_lances_livres(db, season, limit=10):
    return buscar_top_jogadores_por_stat(db=db, season=season, stat_field=PlayerGameStats.ftm, stat_label="free_throws_made", limit=limit)

def buscar_top_rebotes_ofensivos(db, season, limit=10):
    return buscar_top_jogadores_por_stat(db=db, season=season, stat_field=PlayerGameStats.off_reb, stat_label="offensive_rebounds", limit=limit)

def buscar_top_rebotes_defensivos(db, season, limit=10):
    return buscar_top_jogadores_por_stat(db=db, season=season, stat_field=PlayerGameStats.def_reb, stat_label="defensive_rebounds", limit=limit)

def buscar_top_faltas_pessoais(db, season, limit=10):
    return buscar_top_jogadores_por_stat(db=db, season=season, stat_field=PlayerGameStats.p_fouls, stat_label="personal_fouls", limit=limit)

def buscar_top_plus_minus(db, season, limit=10):
    return buscar_top_jogadores_por_stat(db=db, season=season, stat_field=PlayerGameStats.plus_minus, stat_label="plus_minus", limit=limit)
