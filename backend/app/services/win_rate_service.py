import logging

from sqlalchemy.orm import Session

from app.db.models import Game, PlayerGameStats, Prediction

logger = logging.getLogger(__name__)

MARGEM_PONTOS      = 5.0
MARGEM_ASSISTENCIAS = 2.5
MARGEM_REBOTES     = 3.0
MARGEM_ROUBOS      = 1.5 
MARGEM_BLOQUEIOS   = 1.5

def _calcular_win_rate(predicoes_reais, campo_predicao, campo_real, margem):
    total = 0
    acertos = 0
    soma_erros = 0.0

    for predicao, stat_real in predicoes_reais:
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

    if total == 0:
        return {
            "total_avaliadas": 0,
            "total_acertos": 0, 
            "win_rate": 0.0, 
            "mae_medio": None, 
            "margem_tolerancia": margem
            }

    win_rate = round((acertos / total) * 100, 2)
    mae = round(soma_erros / total, 2)

    return {
        "total_avaliadas": total,
        "total_acertos": acertos,
        "win_rate": win_rate,
        "mae_medio": mae,
        "margem_tolerancia": margem,
    }

def calcular_win_rate(db: Session, temporada: int):
    resultados = (
        db.query(Prediction, PlayerGameStats)
        .join(PlayerGameStats, (PlayerGameStats.player_id == Prediction.player_id) & (PlayerGameStats.game_id == Prediction.game_id))
        .join(Game, Game.id == Prediction.game_id)
        .filter(Prediction.season == temporada, Game.status_short == 3).all()
    )

    if not resultados:
        logger.warning(f"Nenhuma predição avaliável encontrada para a temporada {temporada}.")
        return None

    desempenho_pontos = _calcular_win_rate(resultados, "predicted_points", "points", MARGEM_PONTOS)
    desempenho_assistencias = _calcular_win_rate(resultados, "predicted_assists", "assists", MARGEM_ASSISTENCIAS)
    desempenho_rebotes = _calcular_win_rate(resultados, "predicted_rebounds", "tot_reb", MARGEM_REBOTES)
    desempenho_roubos = _calcular_win_rate(resultados, "predicted_steals", "steals", MARGEM_ROUBOS)
    desempenho_bloqueios = _calcular_win_rate(resultados, "predicted_blocks", "blocks", MARGEM_BLOQUEIOS)

    win_rates_com_dados = []
    maes_com_dados = []

    for desempenho in [desempenho_pontos, desempenho_assistencias, desempenho_rebotes, desempenho_roubos, desempenho_bloqueios]:
        if desempenho["total_avaliadas"] > 0:
            win_rates_com_dados.append(desempenho["win_rate"])
            if desempenho["mae_medio"] is not None:
                maes_com_dados.append(desempenho["mae_medio"])

    if not win_rates_com_dados:
        win_rate_geral = 0.0
    else:
        win_rate_geral = round(sum(win_rates_com_dados) / len(win_rates_com_dados), 2)

    if not maes_com_dados:
        mae_geral = None
    else:
        mae_geral = round(sum(maes_com_dados) / len(maes_com_dados), 2)

    return {
        "temporada": temporada,
        "total_predicoes_avaliadas": len(resultados),
        "win_rate_geral": win_rate_geral,
        "mae_medio_geral": mae_geral,
        "pontos":       desempenho_pontos,
        "assistencias": desempenho_assistencias,
        "rebotes":      desempenho_rebotes,
        "roubos":       desempenho_roubos,
        "bloqueios":    desempenho_bloqueios,
    }