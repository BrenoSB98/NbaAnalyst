from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class TeamAvgPointsResponse(BaseModel):
    team_id: int
    team_name: str
    season: int
    total_games: int
    avg_points: float
    avg_points_conceded: float

class PlayerAvgStatsResponse(BaseModel):
    player_id: int
    player_name: str
    season: int
    total_games: int
    avg_points: float
    avg_assists: float
    avg_rebounds: float
    avg_steals: float
    avg_blocks: float

class TeamLastGamesResponse(BaseModel):
    team_id: int
    team_name: str
    game_id: int
    date: Optional[datetime]
    opponent: str
    points_scored: Optional[int]
    points_conceded: Optional[int]
    win: Optional[bool]

class MediasJogador(BaseModel):
    pontos: Optional[float] = None
    assistencias: Optional[float] = None
    rebotes: Optional[float] = None
    roubos: Optional[float] = None
    bloqueios: Optional[float] = None
    turnovers: Optional[float] = None
    fg_pct: Optional[float] = None
    three_pct: Optional[float] = None
    ft_pct: Optional[float] = None

class AnalyticsSummary(BaseModel):
    jogador_id: int
    nome_jogador: str
    temporada: int
    jogos_analisados: int
    medias: MediasJogador

class ResultadoJogo(BaseModel):
    game_id: int
    data: Optional[datetime] = None
    real: float
    predicao: float
    erro_absoluto: float

class BacktestMetrics(BaseModel):
    jogador_id: int
    nome_jogador: str
    temporada: int
    estatistica: str
    total_testes: int
    erro_medio_absoluto: Optional[float] = None
    resultados_detalhados: List[ResultadoJogo]