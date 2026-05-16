from datetime import datetime, timezone
from unittest.mock import MagicMock, call, patch
import pytest

with patch("sqlalchemy.create_engine", return_value=MagicMock()):
    from app.services.manager_service import _converter_minutos, _filtrar_jogadores_ativos
    from app.services.analytics_service import calcular_totais_e_medias


def _criar_stat(points=20, assists=5, tot_reb=8, steals=2, blocks=1,
                turnovers=3, minutes=30, fgm=7, fga=14, tpm=2, tpa=5,
                ftm=4, fta=5, off_reb=2, def_reb=6, p_fouls=2, plus_minus=5):
    stat = MagicMock()
    stat.points = points
    stat.assists = assists
    stat.tot_reb = tot_reb
    stat.steals = steals
    stat.blocks = blocks
    stat.turnovers = turnovers
    stat.minutes = minutes
    stat.fgm = fgm
    stat.fga = fga
    stat.tpm = tpm
    stat.tpa = tpa
    stat.ftm = ftm
    stat.fta = fta
    stat.off_reb = off_reb
    stat.def_reb = def_reb
    stat.p_fouls = p_fouls
    stat.plus_minus = plus_minus
    return stat


def _criar_jogo(game_id=1, date_start=None):
    jogo = MagicMock()
    jogo.id = game_id
    jogo.date_start = date_start or datetime(2025, 1, 15, tzinfo=timezone.utc)
    return jogo


class TestConverterMinutos:
    def test_formato_mm_ss(self):
        assert _converter_minutos("32:30") == pytest.approx(32.5, rel=1e-3)

    def test_formato_zero(self):
        assert _converter_minutos("0:00") == 0.0

    def test_formato_zerozero_zerozero(self):
        assert _converter_minutos("00:00") == 0.0

    def test_none(self):
        assert _converter_minutos(None) == 0.0

    def test_string_vazia(self):
        assert _converter_minutos("") == 0.0

    def test_float_string(self):
        assert _converter_minutos("25.5") == 25.5

    def test_formato_apenas_minutos_sem_segundos(self):
        assert _converter_minutos("30:00") == 30.0

    def test_string_invalida(self):
        assert _converter_minutos("abc:def") == 0.0

    def test_um_segundo(self):
        resultado = _converter_minutos("0:01")
        assert resultado == pytest.approx(1 / 60, rel=1e-3)

    def test_quarenta_e_oito_minutos(self):
        assert _converter_minutos("48:00") == 48.0


class TestFiltrarJogadoresAtivos:
    def test_sem_jogos_retorna_lista_original(self):
        db = MagicMock()
        # Simula nenhum jogo recente → deve retornar player_ids original
        db.execute.return_value.scalars.return_value.all.return_value = []

        resultado = _filtrar_jogadores_ativos(db, player_ids=[1, 2, 3], team_id=1, season=2025)

        assert resultado == [1, 2, 3]

    def test_jogadores_que_jogaram(self):
        db = MagicMock()

        jogo_mock = MagicMock()
        jogo_mock.id = 100

        stat_mock = MagicMock()
        stat_mock.minutes = "30:00"

        # Primeiro execute: busca jogos → retorna [jogo_mock]
        # Segundo execute (player_id=1): busca stats → retorna [stat_mock] (jogou)
        # Terceiro execute (player_id=2): busca stats → retorna [] (não jogou)
        resultados = [
            [jogo_mock],
            [stat_mock],
            [],
        ]
        indice = [0]

        def execute_side_effect(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = resultados[indice[0]]
            indice[0] = indice[0] + 1
            return mock_result

        db.execute.side_effect = execute_side_effect

        resultado = _filtrar_jogadores_ativos(db, player_ids=[1, 2], team_id=1, season=2025)

        assert 1 in resultado
        assert 2 not in resultado


class TestCalcularTotaisEMedias:
    def test_lista_vazia_retorna_none(self):
        assert calcular_totais_e_medias([]) is None

    def test_um_jogo_medias_iguais_ao_jogo(self):
        stat = _criar_stat(points=20, assists=5)
        jogo = _criar_jogo()
        resultado = calcular_totais_e_medias([(stat, jogo)])

        assert resultado["num_jogos"] == 1
        assert resultado["averages"]["points"] == 20.0
        assert resultado["averages"]["assists"] == 5.0

    def test_dois_jogos_media_correta(self):
        stat1 = _criar_stat(points=20)
        stat2 = _criar_stat(points=30)
        resultado = calcular_totais_e_medias([(stat1, _criar_jogo(1)), (stat2, _criar_jogo(2))])

        assert resultado["num_jogos"] == 2
        assert resultado["averages"]["points"] == 25.0

    def test_totais_corretos(self):
        stat1 = _criar_stat(points=10, assists=3)
        stat2 = _criar_stat(points=20, assists=7)
        resultado = calcular_totais_e_medias([(stat1, _criar_jogo(1)), (stat2, _criar_jogo(2))])

        assert resultado["totals"]["points"] == 30
        assert resultado["totals"]["assists"] == 10

    def test_fg_pct_calculado(self):
        stat = _criar_stat(fgm=5, fga=10)
        resultado = calcular_totais_e_medias([(stat, _criar_jogo())])
        assert resultado["averages"]["fg_pct"] == pytest.approx(50.0, rel=1e-2)

    def test_fg_pct_zero_quando_sem_tentativas(self):
        stat = _criar_stat(fgm=0, fga=0)
        resultado = calcular_totais_e_medias([(stat, _criar_jogo())])
        assert resultado["averages"]["fg_pct"] == 0

    def test_num_jogos_correto(self):
        dados = [((_criar_stat(), _criar_jogo(i))) for i in range(5)]
        resultado = calcular_totais_e_medias(dados)
        assert resultado["num_jogos"] == 5

    def test_retorna_lista_de_jogos(self):
        stat = _criar_stat(points=25)
        jogo = _criar_jogo(game_id=999)
        resultado = calcular_totais_e_medias([(stat, jogo)])
        assert len(resultado["games"]) == 1
        assert resultado["games"][0]["game_id"] == 999

    def test_stat_none_tratado_como_zero(self):
        stat = _criar_stat(points=None, assists=None)
        resultado = calcular_totais_e_medias([(stat, _criar_jogo())])
        assert resultado["totals"]["points"] == 0
        assert resultado["totals"]["assists"] == 0