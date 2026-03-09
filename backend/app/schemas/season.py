from pydantic import BaseModel, ConfigDict

class SeasonBase(BaseModel):
    season: int

class SeasonOut(SeasonBase):
    model_config = ConfigDict(from_attributes=True)