from unittest.mock import MagicMock, patch
import pytest

with patch("sqlalchemy.create_engine", return_value=MagicMock()):
    from app.services.confronto_service import (
        _buscar_time,
        _buscar_stats_do_time_no_jogo,
        _buscar_score_do_time_no_jogo,
        _calcular_dados_confronto,
    )


def _db_retorna(valor):
    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = valor
    return db

def _db_retorna_lista(valor):
    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = valor
    return db


class TestBuscarTime:
    def test_time_encontrado(self):
        time_mock = MagicMock()
        time_mock.name = "Boston Celtics"
        time_mock.id = 2
        db = _db_retorna(time_mock)

        resultado = _buscar_time(db, time_id=2)

        assert resultado.name == "Boston Celtics"
        assert resultado.id == 2

    def test_time_nao_encontrado(self):
        db = _db_retorna(None)

        resultado = _buscar_time(db, time_id=999)

        assert resultado is None


class TestBuscarStatsDoTimeNoJogo:
    def test_stats_encontradas(self):
        stats_mock = MagicMock()
        stats_mock.points = 110
        stats_mock.assists = 25
        db = _db_retorna(stats_mock)

        resultado = _buscar_stats_do_time_no_jogo(db, game_id=1001, team_id=1)

        assert resultado.points == 110
        assert resultado.assists == 25

    def test_stats_nao_encontradas(self):
        db = _db_retorna(None)

        resultado = _buscar_stats_do_time_no_jogo(db, game_id=1001, team_id=999)

        assert resultado is None


class TestBuscarScoreDoTimeNoJogo:
    def test_score_encontrado(self):
        score_mock = MagicMock()
        score_mock.points = 105
        score_mock.is_home = True
        db = _db_retorna(score_mock)

        resultado = _buscar_score_do_time_no_jogo(db, game_id=1001, team_id=1)

        assert resultado.points == 105
        assert resultado.is_home is True

    def test_score_nao_encontrado(self):
        db = _db_retorna(None)

        resultado = _buscar_score_do_time_no_jogo(db, game_id=1001, team_id=999)

        assert resultado is None


class TestCalcularDadosConfronto:
    def test_sem_jogos_retorna_historico_zerado(self):
        db = MagicMock()
        resultado = _calcular_dados_confronto(db, time_casa_id=1, time_fora_id=2, jogos=[])

        assert resultado["total_jogos"] == 0
        assert resultado["vitorias_casa"] == 0
        assert resultado["vitorias_fora"] == 0
        assert resultado["medias_casa"] is None
        assert resultado["medias_fora"] is None

    def test_vitoria_time_casa(self):
        jogo = MagicMock()
        jogo.id = 1001

        stats_casa = MagicMock()
        stats_casa.points = 110
        stats_casa.assists = 25
        stats_casa.tot_reb = 40
        stats_casa.steals = 8
        stats_casa.blocks = 5
        stats_casa.turnovers = 12
        stats_casa.plus_minus = 10
        stats_casa.fgp = 48.0
        stats_casa.tpp = 35.0
        stats_casa.ftp = 80.0

        stats_fora = MagicMock()
        stats_fora.points = 98
        stats_fora.assists = 20
        stats_fora.tot_reb = 35
        stats_fora.steals = 6
        stats_fora.blocks = 3
        stats_fora.turnovers = 14
        stats_fora.plus_minus = -10
        stats_fora.fgp = 44.0
        stats_fora.tpp = 30.0
        stats_fora.ftp = 75.0

        score_casa = MagicMock()
        score_casa.points = 110

        score_fora = MagicMock()
        score_fora.points = 98

        db = MagicMock()
        respostas = iter([stats_casa, stats_fora, score_casa, score_fora])
        db.execute.return_value.scalar_one_or_none.side_effect = lambda: next(respostas)

        resultado = _calcular_dados_confronto(db, time_casa_id=1, time_fora_id=2, jogos=[jogo])

        assert resultado["vitorias_casa"] == 1
        assert resultado["vitorias_fora"] == 0
        assert resultado["total_jogos"] == 1