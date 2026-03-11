from typing import List

from pydantic import BaseModel, ConfigDict

class SeasonBase(BaseModel):
    season: int

class SeasonOut(SeasonBase):
    model_config = ConfigDict(from_attributes=True)

class SeasonItem(BaseModel):
    season: int

class TemporadasResponse(BaseModel):
    total: int
    temporadas: List[SeasonItem]