import logging
import math

from app.db.models import Game, PlayerGameStats, Prediction
from app.services.formatar_palpites import verificar_acerto_linha

logger = logging.getLogger(__name__)

def _jogador_teve_minutos(stat_real):
    minutos = stat_real.minutes
    if not minutos:
        return False
    minutos_limpo = str(minutos).strip()
    if minutos_limpo in ("", "0:00", "00:00"):
        return False
    if ":" in minutos_limpo:
        partes = minutos_limpo.split(":")
        if int(partes[0]) == 0 and int(partes[1]) == 0:
            return False
    return True

def _calcular_win_rate_stat(predicoes_reais, campo_predicao, campo_real):
    total = 0
    acertos = 0
    soma_erros = 0.0
    soma_erros_quadraticos = 0.0
    ignorados_sem_minutos = 0

    for palpite, stat_real in predicoes_reais:
        if not _jogador_teve_minutos(stat_real):
            ignorados_sem_minutos = ignorados_sem_minutos + 1
            continue

        valor_previsto = getattr(palpite, campo_predicao, None)
        valor_real = getattr(stat_real, campo_real, None)

        if valor_previsto is None or valor_real is None:
            continue

        total = total + 1
        erro = abs(float(valor_previsto) - float(valor_real))
        soma_erros = soma_erros + erro
        soma_erros_quadraticos = soma_erros_quadraticos + (erro ** 2)

        acertou = verificar_acerto_linha(valor_previsto, valor_real)
        if acertou:
            acertos = acertos + 1

    if ignorados_sem_minutos > 0:
        logger.warning(f"Palpites ignorados por falta de minutos, total={ignorados_sem_minutos}, campo={campo_real}")

    if total == 0:
        return {
            "total_avaliadas": 0,
            "total_acertos": 0,
            "win_rate": 0.0,
            "mae_medio": None,
            "rmse": None,
        }

    win_rate = round((acertos / total) * 100, 2)
    mae = round(soma_erros / total, 2)
    rmse = round(math.sqrt(soma_erros_quadraticos / total), 2)

    return {
        "total_avaliadas": total,
        "total_acertos": acertos,
        "win_rate": win_rate,
        "mae_medio": mae,
        "rmse": rmse,
    }


def calcular_win_rate(db, temporada):
    palpites_com_real = (
        db.query(Prediction, PlayerGameStats)
        .join(PlayerGameStats, (PlayerGameStats.player_id == Prediction.player_id) & (PlayerGameStats.game_id == Prediction.game_id))
        .join(Game, Game.id == Prediction.game_id)
        .filter(Prediction.season == temporada, Game.status_short == 3)
        .all()
    )

    if not palpites_com_real:
        logger.warning(f"Nenhum palpite avaliável, temporada={temporada}")
        return None

    desempenho_pontos = _calcular_win_rate_stat(palpites_com_real, "predicted_points", "points")
    desempenho_assistencias = _calcular_win_rate_stat(palpites_com_real, "predicted_assists", "assists")
    desempenho_rebotes = _calcular_win_rate_stat(palpites_com_real, "predicted_rebounds", "tot_reb")
    desempenho_roubos = _calcular_win_rate_stat(palpites_com_real, "predicted_steals", "steals")
    desempenho_bloqueios = _calcular_win_rate_stat(palpites_com_real, "predicted_blocks", "blocks")

    lista_desempenhos = [desempenho_pontos, desempenho_assistencias, desempenho_rebotes, desempenho_roubos, desempenho_bloqueios]

    soma_win_rates = 0.0
    soma_maes = 0.0
    soma_rmses = 0.0
    qtd_com_dados = 0
    qtd_com_mae = 0
    qtd_com_rmse = 0

    for d in lista_desempenhos:
        if d["total_avaliadas"] > 0:
            soma_win_rates = soma_win_rates + d["win_rate"]
            qtd_com_dados = qtd_com_dados + 1
            if d["mae_medio"] is not None:
                soma_maes = soma_maes + d["mae_medio"]
                qtd_com_mae = qtd_com_mae + 1
            if d["rmse"] is not None:
                soma_rmses = soma_rmses + d["rmse"]
                qtd_com_rmse = qtd_com_rmse + 1

    if qtd_com_dados > 0:
        win_rate_geral = round(soma_win_rates / qtd_com_dados, 2)
    else:
        win_rate_geral = 0.0

    if qtd_com_mae > 0:
        mae_geral = round(soma_maes / qtd_com_mae, 2)
    else:
        mae_geral = None

    if qtd_com_rmse > 0:
        rmse_geral = round(soma_rmses / qtd_com_rmse, 2)
    else:
        rmse_geral = None

    return {
        "temporada": temporada,
        "total_predicoes_avaliadas": len(palpites_com_real),
        "win_rate_geral": win_rate_geral,
        "mae_medio_geral": mae_geral,
        "rmse_geral": rmse_geral,
        "pontos": desempenho_pontos,
        "assistencias": desempenho_assistencias,
        "rebotes": desempenho_rebotes,
        "roubos": desempenho_roubos,
        "bloqueios": desempenho_bloqueios,
    }