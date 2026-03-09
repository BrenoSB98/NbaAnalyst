from typing import Optional
from pydantic import BaseModel, ConfigDict

class LeagueBase(BaseModel):
    code: str
    description: Optional[str] = None

class LeagueOut(LeagueBase):
    id: int

    model_config = ConfigDict(from_attributes=True)