import logging

from app.db.models import Game, GameTeamScore, GameTeamStats, Team

logger = logging.getLogger(__name__)

def _buscar_time(db, time_id):
    time = db.query(Team).filter(Team.id == time_id).first()
    return time

def _buscar_ultimos_jogos_head_to_head(db, time_casa_id, time_fora_id, ultimos_n):
    jogos = (db.query(Game).filter(Game.status_short == 3, (((Game.home_team_id == time_casa_id) & (Game.away_team_id == time_fora_id)) |
                                                            ((Game.home_team_id == time_fora_id) & (Game.away_team_id == time_casa_id)))).order_by(Game.date_start.desc()).limit(ultimos_n).all())
    return jogos

def _buscar_stats_do_time_no_jogo(db, game_id, team_id):
    stats = db.query(GameTeamStats).filter(GameTeamStats.game_id == game_id, GameTeamStats.team_id == team_id).first()
    return stats

def _buscar_score_do_time_no_jogo(db, game_id, team_id):
    score = db.query(GameTeamScore).filter(GameTeamScore.game_id == game_id, GameTeamScore.team_id == team_id).first()
    return score

def _calcular_dados_confronto(db, time_casa_id, time_fora_id, jogos):
    vitorias_casa = 0
    vitorias_fora = 0

    total_pts_casa = 0
    total_pts_sofridos_casa = 0
    total_reb_casa = 0
    total_ast_casa = 0
    total_stl_casa = 0
    total_blk_casa = 0
    total_tov_casa = 0
    total_pm_casa = 0
    total_fgp_casa = 0
    total_tpp_casa = 0
    total_ftp_casa = 0

    total_pts_fora = 0
    total_pts_sofridos_fora = 0
    total_reb_fora = 0
    total_ast_fora = 0
    total_stl_fora = 0
    total_blk_fora = 0
    total_tov_fora = 0
    total_pm_fora = 0
    total_fgp_fora = 0
    total_tpp_fora = 0
    total_ftp_fora = 0

    jogos_com_dados = 0

    for jogo in jogos:
        stats_casa = _buscar_stats_do_time_no_jogo(db, jogo.id, time_casa_id)
        stats_fora = _buscar_stats_do_time_no_jogo(db, jogo.id, time_fora_id)

        if not stats_casa or not stats_fora:
            continue

        score_casa = _buscar_score_do_time_no_jogo(db, jogo.id, time_casa_id)
        score_fora = _buscar_score_do_time_no_jogo(db, jogo.id, time_fora_id)
        if score_casa and score_fora:
            pts_placar_casa = score_casa.points or 0
            pts_placar_fora = score_fora.points or 0

            if pts_placar_casa > pts_placar_fora:
                vitorias_casa = vitorias_casa + 1
            elif pts_placar_fora > pts_placar_casa:
                vitorias_fora = vitorias_fora + 1

        total_pts_casa = total_pts_casa + (stats_casa.points or 0)
        total_pts_sofridos_casa = total_pts_sofridos_casa + (stats_fora.points or 0)
        total_reb_casa = total_reb_casa + (stats_casa.tot_reb or 0)
        total_ast_casa = total_ast_casa + (stats_casa.assists or 0)
        total_stl_casa = total_stl_casa + (stats_casa.steals or 0)
        total_blk_casa = total_blk_casa + (stats_casa.blocks or 0)
        total_tov_casa = total_tov_casa + (stats_casa.turnovers or 0)
        total_pm_casa = total_pm_casa + (stats_casa.plus_minus or 0)
        total_fgp_casa = total_fgp_casa + float(stats_casa.fgp or 0)
        total_tpp_casa = total_tpp_casa + float(stats_casa.tpp or 0)
        total_ftp_casa = total_ftp_casa + float(stats_casa.ftp or 0)

        total_pts_fora = total_pts_fora + (stats_fora.points or 0)
        total_pts_sofridos_fora = total_pts_sofridos_fora + (stats_casa.points or 0)
        total_reb_fora = total_reb_fora + (stats_fora.tot_reb or 0)
        total_ast_fora = total_ast_fora + (stats_fora.assists or 0)
        total_stl_fora = total_stl_fora + (stats_fora.steals or 0)
        total_blk_fora = total_blk_fora + (stats_fora.blocks or 0)
        total_tov_fora = total_tov_fora + (stats_fora.turnovers or 0)
        total_pm_fora = total_pm_fora + (stats_fora.plus_minus or 0)
        total_fgp_fora = total_fgp_fora + float(stats_fora.fgp or 0)
        total_tpp_fora = total_tpp_fora + float(stats_fora.tpp or 0)
        total_ftp_fora = total_ftp_fora + float(stats_fora.ftp or 0)

        jogos_com_dados = jogos_com_dados + 1

    resultado = {}
    resultado["total_jogos"] = jogos_com_dados
    resultado["vitorias_casa"] = vitorias_casa
    resultado["vitorias_fora"] = vitorias_fora

    if jogos_com_dados == 0:
        resultado["medias_casa"] = None
        resultado["medias_fora"] = None
        return resultado

    medias_casa = {}
    medias_casa["jogos_considerados"] = jogos_com_dados
    medias_casa["pontos_feitos"] = round(total_pts_casa / jogos_com_dados, 1)
    medias_casa["pontos_sofridos"] = round(total_pts_sofridos_casa / jogos_com_dados, 1)
    medias_casa["rebotes"] = round(total_reb_casa / jogos_com_dados, 1)
    medias_casa["assistencias"] = round(total_ast_casa / jogos_com_dados, 1)
    medias_casa["roubos"] = round(total_stl_casa / jogos_com_dados, 1)
    medias_casa["bloqueios"] = round(total_blk_casa / jogos_com_dados, 1)
    medias_casa["turnovers"] = round(total_tov_casa / jogos_com_dados, 1)
    medias_casa["plus_minus"] = round(total_pm_casa / jogos_com_dados, 1)
    medias_casa["fg_pct"] = round(total_fgp_casa / jogos_com_dados, 1)
    medias_casa["three_pct"] = round(total_tpp_casa / jogos_com_dados, 1)
    medias_casa["ft_pct"] = round(total_ftp_casa / jogos_com_dados, 1)

    medias_fora = {}
    medias_fora["jogos_considerados"] = jogos_com_dados
    medias_fora["pontos_feitos"] = round(total_pts_fora / jogos_com_dados, 1)
    medias_fora["pontos_sofridos"] = round(total_pts_sofridos_fora / jogos_com_dados, 1)
    medias_fora["rebotes"] = round(total_reb_fora / jogos_com_dados, 1)
    medias_fora["assistencias"] = round(total_ast_fora / jogos_com_dados, 1)
    medias_fora["roubos"] = round(total_stl_fora / jogos_com_dados, 1)
    medias_fora["bloqueios"] = round(total_blk_fora / jogos_com_dados, 1)
    medias_fora["turnovers"] = round(total_tov_fora / jogos_com_dados, 1)
    medias_fora["plus_minus"] = round(total_pm_fora / jogos_com_dados, 1)
    medias_fora["fg_pct"] = round(total_fgp_fora / jogos_com_dados, 1)
    medias_fora["three_pct"] = round(total_tpp_fora / jogos_com_dados, 1)
    medias_fora["ft_pct"] = round(total_ftp_fora / jogos_com_dados, 1)

    resultado["medias_casa"] = medias_casa
    resultado["medias_fora"] = medias_fora

    return resultado

def analisar_confronto(db, time_casa_id, time_fora_id, ultimos_n):
    time_casa = _buscar_time(db, time_casa_id)
    time_fora = _buscar_time(db, time_fora_id)

    if not time_casa:
        logger.warning(f"Time casa nao encontrado —> time_casa_id={time_casa_id}")
        return None
    if not time_fora:
        logger.warning(f"Time fora nao encontrado —> time_fora_id={time_fora_id}")
        return None

    jogos = _buscar_ultimos_jogos_head_to_head(db, time_casa_id, time_fora_id, ultimos_n)
    dados = _calcular_dados_confronto(db, time_casa_id, time_fora_id, jogos)

    info_casa = {}
    info_casa["id"] = time_casa.id
    info_casa["nome"] = time_casa.name
    info_casa["apelido"] = time_casa.nickname or ""
    info_casa["codigo"] = time_casa.code or ""
    info_casa["logo"] = time_casa.logo or ""
    info_casa["medias"] = dados["medias_casa"]

    info_fora = {}
    info_fora["id"] = time_fora.id
    info_fora["nome"] = time_fora.name
    info_fora["apelido"] = time_fora.nickname or ""
    info_fora["codigo"] = time_fora.code or ""
    info_fora["logo"] = time_fora.logo or ""
    info_fora["medias"] = dados["medias_fora"]

    historico = {}
    historico["total_jogos"] = dados["total_jogos"]
    historico["vitorias_casa"] = dados["vitorias_casa"]
    historico["vitorias_fora"] = dados["vitorias_fora"]

    resultado = {}
    resultado["ultimos_n"] = ultimos_n
    resultado["historico_confronto"] = historico
    resultado["time_casa"] = info_casa
    resultado["time_fora"] = info_fora

    return resultado