from typing import Optional
from pydantic import BaseModel

class WinRate(BaseModel):
    total_avaliadas: int
    total_acertos: int
    win_rate: float
    mae_medio: Optional[float] = None
    rmse: Optional[float] = None

class WinRateResponse(BaseModel):
    temporada: int
    total_predicoes_avaliadas: int
    win_rate_geral: float
    mae_medio_geral: Optional[float] = None
    rmse_geral: Optional[float] = None
    pontos: WinRate
    assistencias: WinRate
    rebotes: WinRate
    roubos: WinRate
    bloqueios: WinRate