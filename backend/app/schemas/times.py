from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class LeagueInfoResponse(BaseModel):
    league_code: Optional[str] = None
    conference: Optional[str] = None
    division: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class TeamResponse(BaseModel):
    id: int
    name: str
    nickname: Optional[str] = None
    code: Optional[str] = None
    city: Optional[str] = None
    logo: Optional[str] = None
    all_star: Optional[bool] = False
    nba_franchise: Optional[bool] = True

    model_config = ConfigDict(from_attributes=True)

class TeamDetailResponse(TeamResponse):
    league_info: Optional[LeagueInfoResponse] = None

    model_config = ConfigDict(from_attributes=True)

class TeamListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    teams: List[TeamResponse]

    model_config = ConfigDict(from_attributes=True)