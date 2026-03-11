from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict

class LiderEstatistica(BaseModel):
    jogador_id: int
    nome_jogador: str
    temporada: int
    jogos_disputados: int
    valor_total: Optional[float] = None
    media: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class LideresResponse(BaseModel):
    temporada: int
    total: int
    lideres: List[LiderEstatistica]

class MediasAvancadas(BaseModel):
    pontos: Optional[float] = None
    assistencias: Optional[float] = None
    rebotes: Optional[float] = None
    roubos: Optional[float] = None
    bloqueios: Optional[float] = None
    turnovers: Optional[float] = None
    fg_pct: Optional[float] = None
    three_pct: Optional[float] = None
    ft_pct: Optional[float] = None

class MediasUltimosJogosResponse(BaseModel):
    jogador_id: int
    nome_jogador: str
    n_jogos: Optional[int] = None
    jogos_analisados: Optional[int] = None
    temporada: Optional[int] = None
    medias: Optional[MediasAvancadas] = None
    mensagem: Optional[str] = None

class MediasCasaForaResponse(BaseModel):
    jogador_id: int
    nome_jogador: str
    temporada: int
    local: str
    medias: Optional[MediasAvancadas] = None
    mensagem: Optional[str] = None

class MediasTemporadaResponse(BaseModel):
    jogador_id: int
    nome_jogador: str
    temporada: int
    medias: Optional[MediasAvancadas] = None
    mensagem: Optional[str] = None

class MediasContraTimeResponse(BaseModel):
    jogador_id: int
    nome_jogador: str
    time_adversario_id: int
    nome_adversario: str
    temporada: Optional[int] = None
    medias: Optional[MediasAvancadas] = None
    mensagem: Optional[str] = None

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

class MaiorPontuadorItem(BaseModel):
    jogador_id: int
    nome_jogador: str
    jogos_disputados: int
    total_pontos: Optional[int] = None
    media_pontos: float

    model_config = ConfigDict(from_attributes=True)

class MaioresPontuadoresResponse(BaseModel):
    temporada: int
    total: int
    maiores_pontuadores: List[MaiorPontuadorItem]

class TendenciasTimeResponse(BaseModel):
    time_id: int
    nome_time: str
    temporada: int
    ultimos_n_jogos: int
    record: str
    aproveitamento: float
    media_pontos_feitos: float
    media_pontos_sofridos: float
    diferencial_pontos: float
    tendencia_ofensiva: str
    tendencia_defensiva: str