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

class GerarPredicaoResponse(BaseModel):
    mensagem: str
    temporada: int
    total_predicoes_geradas: int