import pytest
from unittest.mock import MagicMock

from app.services.confronto_service import _buscar_time, _buscar_stats_do_time_no_jogo, _buscar_score_do_time_no_jogo, _calcular_dados_confronto

def criar_db_mock():
    return MagicMock()
 
 
def criar_time_mock(time_id, nome):
    time = MagicMock()
    time.id = time_id
    time.name = nome
    return time
 
 
def criar_jogo_mock(jogo_id, home_team_id, away_team_id):
    jogo = MagicMock()
    jogo.id = jogo_id
    jogo.home_team_id = home_team_id
    jogo.away_team_id = away_team_id
    return jogo
 
 
def criar_stats_mock(points=100, tot_reb=40, assists=25, steals=8, blocks=5, turnovers=12, plus_minus=10, fgp=46.5, tpp=35.0, ftp=78.0):
    stats = MagicMock()
    stats.points = points
    stats.tot_reb = tot_reb
    stats.assists = assists
    stats.steals = steals
    stats.blocks = blocks
    stats.turnovers = turnovers
    stats.plus_minus = plus_minus
    stats.fgp = fgp
    stats.tpp = tpp
    stats.ftp = ftp
    return stats
 
 
def criar_score_mock(points):
    score = MagicMock()
    score.points = points
    return score
 
 
class TestBuscarTime:
    def test_time_encontrado(self):
        db = criar_db_mock()
        time = criar_time_mock(1, "Boston Celtics")
        db.query.return_value.filter.return_value.first.return_value = time
 
        resultado = _buscar_time(db, 1)
 
        assert resultado is not None
        assert resultado.name == "Boston Celtics"
 
    def test_time_nao_encontrado(self):
        db = criar_db_mock()
        db.query.return_value.filter.return_value.first.return_value = None
 
        resultado = _buscar_time(db, 99999)
 
        assert resultado is None
 
 
class TestBuscarStatsDoTimeNoJogo:
    def test_stats_encontradas(self):
        db = criar_db_mock()
        stats = criar_stats_mock(points=110)
        db.query.return_value.filter.return_value.first.return_value = stats
 
        resultado = _buscar_stats_do_time_no_jogo(db, game_id=1, team_id=1)
 
        assert resultado is not None
        assert resultado.points == 110
 
    def test_stats_nao_encontradas(self):
        db = criar_db_mock()
        db.query.return_value.filter.return_value.first.return_value = None
 
        resultado = _buscar_stats_do_time_no_jogo(db, game_id=99, team_id=99)
 
        assert resultado is None
 
 
class TestBuscarScoreDoTimeNoJogo:
    def test_score_encontrado(self):
        db = criar_db_mock()
        score = criar_score_mock(points=105)
        db.query.return_value.filter.return_value.first.return_value = score
 
        resultado = _buscar_score_do_time_no_jogo(db, game_id=1, team_id=1)
 
        assert resultado is not None
        assert resultado.points == 105
 
    def test_score_nao_encontrado(self):
        db = criar_db_mock()
        db.query.return_value.filter.return_value.first.return_value = None
 
        resultado = _buscar_score_do_time_no_jogo(db, game_id=99, team_id=99)
 
        assert resultado is None
 
 
class TestCalcularDadosConfronto:
    def _montar_db(self, stats_casa, stats_fora, score_casa_pts, score_fora_pts):
        db = MagicMock()
 
        score_casa = criar_score_mock(score_casa_pts)
        score_fora = criar_score_mock(score_fora_pts)
 
        def side_effect(model):
            mock_query = MagicMock()
 
            def side_filter(*args, **kwargs):
                mock_filter = MagicMock()
 
                call_args = str(args)
                if "GameTeamStats" in str(model):
                    mock_filter.first.side_effect = [stats_casa, stats_fora]
                elif "GameTeamScore" in str(model):
                    mock_filter.first.side_effect = [score_casa, score_fora]
                else:
                    mock_filter.first.return_value = None
 
                return mock_filter
 
            mock_query.filter.side_effect = side_filter
            return mock_query
 
        db.query.side_effect = side
        return db
 
    def test_vitoria_time_casa(self):
        from app.db.models import GameTeamStats, GameTeamScore
 
        db = MagicMock()
        stats_c = criar_stats_mock(points=110)
        stats_f = criar_stats_mock(points=95)
        score_c = criar_score_mock(110)
        score_f = criar_score_mock(95)
 
        call_count = {"n": 0}
 
        def mock_query(model):
            q = MagicMock()
            f = MagicMock()
 
            if model == GameTeamStats:
                call_count["n"] = call_count["n"] + 1
                if call_count["n"] % 2 == 1:
                    f.first.return_value = stats_c
                else:
                    f.first.return_value = stats_f
            elif model == GameTeamScore:
                call_count["n"] = call_count["n"] + 1
                if call_count["n"] % 2 == 1:
                    f.first.return_value = score_c
                else:
                    f.first.return_value = score_f
            else:
                f.first.return_value = None
 
            q.filter.return_value = f
            return q
 
        db.query.side_effect = mock_query
 
        jogo = criar_jogo_mock(jogo_id=1, home_team_id=1, away_team_id=2)
        resultado = _calcular_dados_confronto(db, time_casa_id=1, time_fora_id=2, jogos=[jogo])
 
        assert resultado is not None
        assert "vitorias_casa" in resultado
        assert "vitorias_fora" in resultado
        assert "total_jogos" in resultado
 
    def test_sem_jogos_retorna_historico_zerado(self):
        db = MagicMock()
        resultado = _calcular_dados_confronto(db, time_casa_id=1, time_fora_id=2, jogos=[])
 
        assert resultado is not None
        assert resultado.get("total_jogos", 0) == 0
        assert resultado.get("vitorias_casa", 0) == 0
        assert resultado.get("vitorias_fora", 0) == 0