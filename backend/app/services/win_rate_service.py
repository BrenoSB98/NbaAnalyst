import logging

from app.db.models import Game, PlayerGameStats, Prediction

logger = logging.getLogger(__name__)

MARGEM_PONTOS = 5.0
MARGEM_ASSISTENCIAS = 2.5
MARGEM_REBOTES = 3.0
MARGEM_ROUBOS = 1.5
MARGEM_BLOQUEIOS = 1.5

def _jogador_teve_minutos(stat_real):
    minutos = stat_real.minutes

    if not minutos:
        return False

    minutos_limpo = str(minutos).strip()

    if minutos_limpo == "" or minutos_limpo == "0:00" or minutos_limpo == "00:00":
        return False

    if ":" in minutos_limpo:
        partes = minutos_limpo.split(":")
        if int(partes[0]) == 0 and int(partes[1]) == 0:
            return False

    return True


def _calcular_win_rate_stat(predicoes_reais, campo_predicao, campo_real, margem):
    total = 0
    acertos = 0
    soma_erros = 0.0
    ignorados_sem_minutos = 0

    for predicao, stat_real in predicoes_reais:
        if not _jogador_teve_minutos(stat_real):
            ignorados_sem_minutos = ignorados_sem_minutos + 1
            continue

        valor_previsto = getattr(predicao, campo_predicao, None)
        valor_real = getattr(stat_real, campo_real, None)

        if valor_previsto is None or valor_real is None:
            continue

        valor_previsto_float = float(valor_previsto)
        valor_real_float = float(valor_real)
        erro = abs(valor_previsto_float - valor_real_float)

        soma_erros = soma_erros + erro
        total = total + 1

        if erro <= margem:
            acertos = acertos + 1

    if ignorados_sem_minutos > 0:
        logger.warning(f"Predicoes ignoradas por falta de minutos em quadra —> total={ignorados_sem_minutos}, campo={campo_real}")

    if total == 0:
        resultado = {}
        resultado["total_avaliadas"] = 0
        resultado["total_acertos"] = 0
        resultado["win_rate"] = 0.0
        resultado["mae_medio"] = None
        resultado["margem_tolerancia"] = margem
        return resultado

    win_rate = round((acertos / total) * 100, 2)
    mae = round(soma_erros / total, 2)

    resultado = {}
    resultado["total_avaliadas"] = total
    resultado["total_acertos"] = acertos
    resultado["win_rate"] = win_rate
    resultado["mae_medio"] = mae
    resultado["margem_tolerancia"] = margem
    return resultado


def calcular_win_rate(db, temporada):
    predicoes_com_real = (
        db.query(Prediction, PlayerGameStats)
        .join(PlayerGameStats, (PlayerGameStats.player_id == Prediction.player_id) & (PlayerGameStats.game_id == Prediction.game_id))
        .join(Game, Game.id == Prediction.game_id)
        .filter(Prediction.season == temporada, Game.status_short == 3)
        .all()
    )

    if not predicoes_com_real:
        logger.warning(f"Nenhuma predicao avaliavel encontrada —> temporada={temporada}")
        return None

    desempenho_pontos = _calcular_win_rate_stat(predicoes_com_real, "predicted_points", "points", MARGEM_PONTOS)
    desempenho_assistencias = _calcular_win_rate_stat(predicoes_com_real, "predicted_assists", "assists", MARGEM_ASSISTENCIAS)
    desempenho_rebotes = _calcular_win_rate_stat(predicoes_com_real, "predicted_rebounds", "tot_reb", MARGEM_REBOTES)
    desempenho_roubos = _calcular_win_rate_stat(predicoes_com_real, "predicted_steals", "steals", MARGEM_ROUBOS)
    desempenho_bloqueios = _calcular_win_rate_stat(predicoes_com_real, "predicted_blocks", "blocks", MARGEM_BLOQUEIOS)

    lista_desempenhos = [desempenho_pontos, desempenho_assistencias, desempenho_rebotes, desempenho_roubos, desempenho_bloqueios]

    soma_win_rates = 0.0
    soma_maes = 0.0
    qtd_com_dados = 0
    qtd_com_mae = 0

    for desempenho in lista_desempenhos:
        if desempenho["total_avaliadas"] > 0:
            soma_win_rates = soma_win_rates + desempenho["win_rate"]
            qtd_com_dados = qtd_com_dados + 1

            if desempenho["mae_medio"] is not None:
                soma_maes = soma_maes + desempenho["mae_medio"]
                qtd_com_mae = qtd_com_mae + 1

    if qtd_com_dados == 0:
        win_rate_geral = 0.0
    else:
        win_rate_geral = round(soma_win_rates / qtd_com_dados, 2)

    if qtd_com_mae == 0:
        mae_geral = None
    else:
        mae_geral = round(soma_maes / qtd_com_mae, 2)

    resultado = {}
    resultado["temporada"] = temporada
    resultado["total_predicoes_avaliadas"] = len(predicoes_com_real)
    resultado["win_rate_geral"] = win_rate_geral
    resultado["mae_medio_geral"] = mae_geral
    resultado["pontos"] = desempenho_pontos
    resultado["assistencias"] = desempenho_assistencias
    resultado["rebotes"] = desempenho_rebotes
    resultado["roubos"] = desempenho_roubos
    resultado["bloqueios"] = desempenho_bloqueios

    return resultado