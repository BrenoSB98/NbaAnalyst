from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict

class PredicaoItem(BaseModel):
    prediction_id: int
    game_id: int
    player_id: int
    nome_jogador: str
    nome_time: str
    nome_adversario: str
    eh_casa: Optional[int] = None
    temporada: Optional[int] = None
    pontos_previstos: Optional[float] = None
    assistencias_previstas: Optional[float] = None
    rebotes_previstos: Optional[float] = None
    roubos_previstos: Optional[float] = None
    bloqueios_previstos: Optional[float] = None
    criado_em: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class PredicaoHojeResponse(BaseModel):
    temporada: int
    data: str
    total_jogos: int
    total_predicoes: int
    predicoes: List[PredicaoItem]

class PredicaoItemJogo(BaseModel):
    prediction_id: int
    player_id: int
    nome_jogador: str
    team_id: int
    eh_casa: Optional[int] = None
    pontos_previstos: Optional[float] = None
    assistencias_previstas: Optional[float] = None
    rebotes_previstos: Optional[float] = None
    roubos_previstos: Optional[float] = None
    bloqueios_previstos: Optional[float] = None
    criado_em: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class PredicaoPorJogoResponse(BaseModel):
    game_id: int
    data_inicio: Optional[datetime] = None
    time_casa: str
    time_visitante: str
    total_predicoes: int
    predicoes: List[PredicaoItemJogo]

class PredicaoItemJogador(BaseModel):
    prediction_id: int
    game_id: int
    data_jogo: Optional[datetime] = None
    adversario: str
    eh_casa: Optional[int] = None
    pontos_previstos: Optional[float] = None
    assistencias_previstas: Optional[float] = None
    rebotes_previstos: Optional[float] = None
    roubos_previstos: Optional[float] = None
    bloqueios_previstos: Optional[float] = None
    criado_em: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class PredicaoPorJogadorResponse(BaseModel):
    player_id: int
    nome_jogador: str
    temporada: int
    total_predicoes: int
    predicoes: List[PredicaoItemJogador]

class PredicaoSimples(BaseModel):
    jogador_id: int
    jogador: str
    adversario_id: int
    adversario: str
    temporada: int
    estatistica: str
    eh_casa: int
    previsao: Optional[float] = None

class PredicaoMultiplas(BaseModel):
    jogador_id: int
    jogador: str
    adversario_id: int
    adversario: str
    temporada: int
    eh_casa: int
    previsoes: Optional[dict] = None

class GerarPredicaoResponse(BaseModel):
    mensagem: str
    temporada: int
    total_predicoes_geradas: int