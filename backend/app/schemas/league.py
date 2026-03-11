from typing import Optional, List

from pydantic import BaseModel, ConfigDict

class LeagueBase(BaseModel):
    code: str
    description: Optional[str] = None

class LeagueOut(LeagueBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class LigaItem(BaseModel):
    id: int
    code: str
    descricao: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class LigasResponse(BaseModel):
    total: int
    ligas: List[LigaItem]