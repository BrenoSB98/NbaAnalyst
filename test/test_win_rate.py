import pytest
from unittest.mock import MagicMock

from app.services.win_rate_service import _jogador_teve_minutos, _calcular_win_rate_stat

def criar_stat(minutes):
    stat = MagicMock()
    stat.minutes = minutes
    return stat

def criar_par(previsto, real, minutes="25:30"):
    palpite = MagicMock()
    palpite.predicted_points = previsto
    stat = MagicMock()
    stat.points = real
    stat.minutes = minutes
    return (palpite, stat)

class TestJogadorTeveMinutos:
    def test_minutos_validos(self):
        stat = criar_stat("32:15")
        assert _jogador_teve_minutos(stat) is True

    def test_minutos_zero_zerozero(self):
        stat = criar_stat("0:00")
        assert _jogador_teve_minutos(stat) is False

    def test_minutos_zerozero_zerozero(self):
        stat = criar_stat("00:00")
        assert _jogador_teve_minutos(stat) is False

    def test_minutos_none(self):
        stat = criar_stat(None)
        assert _jogador_teve_minutos(stat) is False

    def test_minutos_string_vazia(self):
        stat = criar_stat("")
        assert _jogador_teve_minutos(stat) is False

    def test_minutos_um_segundo(self):
        stat = criar_stat("0:01")
        assert _jogador_teve_minutos(stat) is True

    def test_minutos_trinta(self):
        stat = criar_stat("30:00")
        assert _jogador_teve_minutos(stat) is True


class TestCalcularWinRateStat:
    def test_todos_acertos(self):
        pares = [
            criar_par(25.0, 25.0),
            criar_par(10.0, 11.0),
            criar_par(15.0, 14.0),
        ]
        resultado = _calcular_win_rate_stat(pares, "predicted_points", "points", margem=3.0)
        assert resultado["total_avaliadas"] == 3
        assert resultado["total_acertos"] == 3
        assert resultado["win_rate"] == 100.0

    def test_nenhum_acerto(self):
        pares = [
            criar_par(5.0, 15.0),
            criar_par(5.0, 20.0),
            criar_par(10.0, 20.0),
        ]
        resultado = _calcular_win_rate_stat(pares, "predicted_points", "points", margem=3.0)
        assert resultado["total_avaliadas"] == 3
        assert resultado["total_acertos"] == 0
        assert resultado["win_rate"] == 0.0

    def test_acerto_parcial(self):
        pares = [
            criar_par(25.0, 25.0),
            criar_par(5.0, 20.0),
            criar_par(10.0, 12.0),
        ]
        resultado = _calcular_win_rate_stat(pares, "predicted_points", "points", margem=3.0)
        assert resultado["total_avaliadas"] == 3
        assert resultado["total_acertos"] == 2
        assert resultado["win_rate"] == round(2 / 3 * 100, 2)

    def test_exatamente_na_margem(self):
        pares = [criar_par(20.0, 23.0)]
        resultado = _calcular_win_rate_stat(pares, "predicted_points", "points", margem=3.0)
        assert resultado["total_acertos"] == 1

    def test_um_acima_da_margem(self):
        pares = [criar_par(20.0, 23.1)]
        resultado = _calcular_win_rate_stat(pares, "predicted_points", "points", margem=3.0)
        assert resultado["total_acertos"] == 0

    def test_ignorar_jogador_sem_minutos(self):
        pares = [
            criar_par(25.0, 25.0, minutes="28:00"),
            criar_par(10.0, 10.0, minutes="0:00"),
        ]
        resultado = _calcular_win_rate_stat(pares, "predicted_points", "points", margem=3.0)
        assert resultado["total_avaliadas"] == 1

    def test_lista_vazia(self):
        resultado = _calcular_win_rate_stat([], "predicted_points", "points", margem=3.0)
        assert resultado["total_avaliadas"] == 0
        assert resultado["win_rate"] == 0.0
        assert resultado["mae_medio"] is None

    def test_mae_calculado(self):
        pares = [
            criar_par(20.0, 24.0),
            criar_par(10.0, 14.0),
        ]
        resultado = _calcular_win_rate_stat(pares, "predicted_points", "points", margem=3.0)
        assert resultado["mae_medio"] == 4.0
        assert resultado["total_avaliadas"] == 2

    def test_retorna_margem_tolerancia(self):
        resultado = _calcular_win_rate_stat([], "predicted_points", "points", margem=2.5)
        assert resultado["margem_tolerancia"] == 2.5

    def test_valor_previsto_none_ignorado(self):
        palpite = MagicMock()
        palpite.predicted_points = None
        stat = MagicMock()
        stat.points = 20
        stat.minutes = "30:00"
        resultado = _calcular_win_rate_stat([(palpite, stat)], "predicted_points", "points", margem=3.0)
        assert resultado["total_avaliadas"] == 0