from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class TeamBase(BaseModel):
    name: str
    nickname: Optional[str] = None
    code: Optional[str] = None
    city: Optional[str] = None
    logo: Optional[str] = None
    all_star: bool = False
    nba_franchise: bool = False

class TeamOut(TeamBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class TeamLeagueInfoBase(BaseModel):
    team_id: int
    league_id: int
    conference: Optional[str] = None
    division: Optional[str] = None

class TeamLeagueInfoOut(TeamLeagueInfoBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

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

class TeamSeasonStatsBase(BaseModel):
    team_id: int
    season: int
    games: Optional[int] = None
    fast_break_points: Optional[int] = None
    points_in_paint: Optional[int] = None
    biggest_lead: Optional[int] = None
    second_chance_points: Optional[int] = None
    points_off_turnovers: Optional[int] = None
    longest_run: Optional[int] = None
    points: Optional[int] = None
    fgm: Optional[int] = None
    fga: Optional[int] = None
    fgp: Optional[float] = None
    ftm: Optional[int] = None
    fta: Optional[int] = None
    ftp: Optional[float] = None
    tpm: Optional[int] = None
    tpa: Optional[int] = None
    tpp: Optional[float] = None
    off_reb: Optional[int] = None
    def_reb: Optional[int] = None
    tot_reb: Optional[int] = None
    assists: Optional[int] = None
    p_fouls: Optional[int] = None
    steals: Optional[int] = None
    turnovers: Optional[int] = None
    blocks: Optional[int] = None
    plus_minus: Optional[int] = None

class TeamSeasonStatsOut(TeamSeasonStatsBase):
    model_config = ConfigDict(from_attributes=True)