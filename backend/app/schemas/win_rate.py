from typing import Optional, Union

from pydantic import BaseModel


class WinRate(BaseModel):
    total_avaliadas: int
    total_acertos: int
    win_rate: float
    mae_medio: Optional[float] = None
    rmse: Optional[float] = None


class Baseline(BaseModel):
    total_avaliadas: int
    total_acertos: int
    win_rate: float


class WinRateResponse(BaseModel):
    temporada: Union[int, str]
    total_predicoes_avaliadas: int
    win_rate_geral: float
    baseline_geral: Optional[float] = None
    ganho_sobre_baseline: Optional[float] = None
    mae_medio_geral: Optional[float] = None
    rmse_geral: Optional[float] = None
    pontos: WinRate
    assistencias: WinRate
    rebotes: WinRate
    roubos: WinRate
    bloqueios: WinRate
    baseline_pontos: Optional[Baseline] = None
    baseline_assistencias: Optional[Baseline] = None
    baseline_rebotes: Optional[Baseline] = None
    baseline_roubos: Optional[Baseline] = None
    baseline_bloqueios: Optional[Baseline] = None
