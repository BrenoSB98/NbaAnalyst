from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest

with patch("sqlalchemy.create_engine", return_value=MagicMock()):
    from app.services.win_rate_service import (
        _jogador_teve_minutos,
        _calcular_win_rate_stat,
    )


def _criar_par(minutos, previsto, real, campo_previsto="predicted_points", campo_real="points"):
    palpite = MagicMock()
    setattr(palpite, campo_previsto, Decimal(str(previsto)) if previsto is not None else None)
    stat = MagicMock()
    setattr(stat, campo_real, real)
    stat.minutes = minutos
    return palpite, stat


class TestJogadorTeveMinutos:
    def test_minutos_validos(self):
        stat = MagicMock()
        stat.minutes = "35:20"
        assert _jogador_teve_minutos(stat) is True

    def test_minutos_zero_zerozero(self):
        stat = MagicMock()
        stat.minutes = "0:00"
        assert _jogador_teve_minutos(stat) is False

    def test_minutos_zerozero_zerozero(self):
        stat = MagicMock()
        stat.minutes = "00:00"
        assert _jogador_teve_minutos(stat) is False

    def test_minutos_none(self):
        stat = MagicMock()
        stat.minutes = None
        assert _jogador_teve_minutos(stat) is False

    def test_minutos_string_vazia(self):
        stat = MagicMock()
        stat.minutes = ""
        assert _jogador_teve_minutos(stat) is False

    def test_minutos_um_segundo(self):
        stat = MagicMock()
        stat.minutes = "0:01"
        assert _jogador_teve_minutos(stat) is True

    def test_minutos_trinta(self):
        stat = MagicMock()
        stat.minutes = "30:00"
        assert _jogador_teve_minutos(stat) is True


class TestCalcularWinRateStat:
    def test_lista_vazia(self):
        resultado = _calcular_win_rate_stat([], "predicted_points", "points")
        assert resultado["total_avaliadas"] == 0
        assert resultado["win_rate"] == 0.0
        assert resultado["mae_medio"] is None

    def test_todos_acertos(self):
        # Previsão 20.7 → linha 20.5 → "mais de" → real 25 >= 20.5 → acerto
        pares = [_criar_par("30:00", 20.7, 25), _criar_par("30:00", 20.7, 22)]
        resultado = _calcular_win_rate_stat(pares, "predicted_points", "points")
        assert resultado["total_acertos"] == 2
        assert resultado["win_rate"] == 100.0

    def test_nenhum_acerto(self):
        # Previsão 20.7 → "mais de" → real 15 < 20.5 → erro
        pares = [_criar_par("30:00", 20.7, 15), _criar_par("30:00", 20.7, 10)]
        resultado = _calcular_win_rate_stat(pares, "predicted_points", "points")
        assert resultado["total_acertos"] == 0
        assert resultado["win_rate"] == 0.0

    def test_acerto_parcial(self):
        pares = [
            _criar_par("30:00", 20.7, 25),
            _criar_par("30:00", 20.7, 15),
        ]
        resultado = _calcular_win_rate_stat(pares, "predicted_points", "points")
        assert resultado["total_acertos"] == 1
        assert resultado["win_rate"] == 50.0

    def test_exatamente_na_linha(self):
        # Previsão 20.7 → linha 20.5 → "mais de" → real 20.5 >= 20.5 → acerto
        pares = [_criar_par("30:00", 20.7, 20.5)]
        resultado = _calcular_win_rate_stat(pares, "predicted_points", "points")
        assert resultado["total_acertos"] == 1

    def test_um_acima_da_linha(self):
        # Previsão 20.7 → linha 20.5 → real 21 >= 20.5 → acerto
        pares = [_criar_par("30:00", 20.7, 21)]
        resultado = _calcular_win_rate_stat(pares, "predicted_points", "points")
        assert resultado["total_acertos"] == 1

    def test_ignorar_jogador_sem_minutos(self):
        pares = [_criar_par("0:00", 20.7, 25)]
        resultado = _calcular_win_rate_stat(pares, "predicted_points", "points")
        assert resultado["total_avaliadas"] == 0

    def test_mae_calculado(self):
        # Previsão 20.0 → real 24.0 → MAE = 4.0
        pares = [_criar_par("30:00", 20.0, 24)]
        resultado = _calcular_win_rate_stat(pares, "predicted_points", "points")
        assert resultado["mae_medio"] == pytest.approx(4.0, rel=1e-2)

    def test_valor_previsto_none_ignorado(self):
        pares = [_criar_par("30:00", None, 25)]
        resultado = _calcular_win_rate_stat(pares, "predicted_points", "points")
        assert resultado["total_avaliadas"] == 0

    def test_win_rate_campos_assistencias(self):
        # Previsão 5.7 → linha 5.5 → "mais de" → real 7 >= 5.5 → acerto
        pares = [_criar_par("30:00", 5.7, 7, "predicted_assists", "assists")]
        resultado = _calcular_win_rate_stat(pares, "predicted_assists", "assists")
        assert resultado["total_acertos"] == 1