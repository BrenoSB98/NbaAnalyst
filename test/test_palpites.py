import pytest
from unittest.mock import MagicMock, patch

from app.services.manager_service import _converter_minutos, _filtrar_jogadores_ativos
from app.services.analytics_service import calcular_totais_e_medias

class TestConverterMinutos:
    def test_formato_mm_ss(self):
        resultado = _converter_minutos("30:45")
        assert resultado == pytest.approx(30.75, rel=1e-3)

    def test_formato_zero(self):
        resultado = _converter_minutos("0:00")
        assert resultado == 0.0

    def test_formato_zerozero_zerozero(self):
        resultado = _converter_minutos("00:00")
        assert resultado == 0.0

    def test_none(self):
        resultado = _converter_minutos(None)
        assert resultado == 0.0

    def test_string_vazia(self):
        resultado = _converter_minutos("")
        assert resultado == 0.0

    def test_float_string(self):
        resultado = _converter_minutos("25.5")
        assert resultado == 25.5

    def test_formato_apenas_minutos_sem_segundos(self):
        resultado = _converter_minutos("20:00")
        assert resultado == 20.0

    def test_string_invalida(self):
        resultado = _converter_minutos("abc:de")
        assert resultado == 0.0

    def test_um_segundo(self):
        resultado = _converter_minutos("0:30")
        assert resultado == pytest.approx(0.5, rel=1e-3)

    def test_quarenta_e_oito_minutos(self):
        resultado = _converter_minutos("48:00")
        assert resultado == 48.0

class TestFiltrarJogadoresAtivos:
    def test_jogadores_que_jogaram(self):
        db = MagicMock()

        jogo1 = MagicMock()
        jogo1.id = 101
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [jogo1]

        stat_pid1 = MagicMock()
        stat_pid1.minutes = "28:00"

        def side_effect_query(model):
            mock = MagicMock()
            mock.filter.return_value.all.return_value = [stat_pid1]
            return mock

        db.query.side_effect = side_effect_query

        resultado = _filtrar_jogadores_ativos(db, player_ids=[1], team_id=10, season=2025)
        assert 1 in resultado

    def test_sem_jogos_retorna_lista_original(self):
        db = MagicMock()

        def side_effect_query(model):
            mock = MagicMock()
            mock.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
            mock.filter.return_value.all.return_value = []
            return mock

        db.query.side_effect = side_effect_query

        resultado = _filtrar_jogadores_ativos(db, player_ids=[1, 2, 3], team_id=10, season=2025)
        assert resultado == [1, 2, 3]

class TestCalcularTotaisEMedias:
    def criar_stat_jogo(self, points=20, assists=5, tot_reb=8, steals=1, blocks=0, turnovers=2, minutes=32, fgm=8, fga=15, tpm=2, tpa=5, ftm=2, fta=2, off_reb=2, def_reb=6, p_fouls=3, plus_minus=5, game_id=1, date_start=None):
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

        jogo = MagicMock()
        jogo.id = game_id
        jogo.date_start = date_start

        return (stat, jogo)

    def test_lista_vazia_retorna_none(self):
        resultado = calcular_totais_e_medias([])
        assert resultado is None

    def test_um_jogo_medias_iguais_ao_jogo(self):
        par = self.criar_stat_jogo(points=30, assists=10, tot_reb=5)
        resultado = calcular_totais_e_medias([par])
        assert resultado is not None
        assert resultado["averages"]["points"] == 30.0
        assert resultado["averages"]["assists"] == 10.0
        assert resultado["averages"]["rebounds"] == 5.0

    def test_dois_jogos_media_correta(self):
        par1 = self.criar_stat_jogo(points=20, assists=4, tot_reb=6, game_id=1)
        par2 = self.criar_stat_jogo(points=30, assists=8, tot_reb=10, game_id=2)
        resultado = calcular_totais_e_medias([par1, par2])
        assert resultado["averages"]["points"] == 25.0
        assert resultado["averages"]["assists"] == 6.0
        assert resultado["averages"]["rebounds"] == 8.0

    def test_totais_corretos(self):
        par1 = self.criar_stat_jogo(points=20, fgm=8, fga=15, game_id=1)
        par2 = self.criar_stat_jogo(points=30, fgm=12, fga=20, game_id=2)
        resultado = calcular_totais_e_medias([par1, par2])
        assert resultado["totals"]["points"] == 50
        assert resultado["totals"]["fgm"] == 20
        assert resultado["totals"]["fga"] == 35

    def test_fg_pct_calculado(self):
        par = self.criar_stat_jogo(fgm=8, fga=16)
        resultado = calcular_totais_e_medias([par])
        assert resultado["averages"]["fg_pct"] == 50.0

    def test_fg_pct_zero_quando_sem_tentativas(self):
        par = self.criar_stat_jogo(fgm=0, fga=0)
        resultado = calcular_totais_e_medias([par])
        assert resultado["averages"]["fg_pct"] == 0

    def test_num_jogos_correto(self):
        pares = [self.criar_stat_jogo(game_id=1), self.criar_stat_jogo(game_id=2), self.criar_stat_jogo(game_id=3)]
        resultado = calcular_totais_e_medias(pares)
        assert resultado["num_jogos"] == 3

    def test_retorna_lista_de_jogos(self):
        par = self.criar_stat_jogo(points=25, game_id=99)
        resultado = calcular_totais_e_medias([par])
        assert len(resultado["games"]) == 1
        assert resultado["games"][0]["game_id"] == 99
        assert resultado["games"][0]["points"] == 25

    def test_stat_none_tratado_como_zero(self):
        par = self.criar_stat_jogo(points=None, assists=None)
        resultado = calcular_totais_e_medias([par])
        assert resultado["averages"]["points"] == 0.0
        assert resultado["averages"]["assists"] == 0.0