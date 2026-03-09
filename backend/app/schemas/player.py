from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict

class PlayerBase(BaseModel):
    firstname: str
    lastname: str
    birth_date: Optional[date] = None
    birth_country: Optional[str] = None
    nba_start: Optional[int] = None
    nba_pro: Optional[int] = None
    height_feet: Optional[int] = None
    height_inches: Optional[int] = None
    height_meters: Optional[float] = None
    weight_pounds: Optional[int] = None
    weight_kilograms: Optional[float] = None
    college: Optional[str] = None
    affiliation: Optional[str] = None

class PlayerOut(PlayerBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class PlayerResponse(BaseModel):
    id: int
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    birth_date: Optional[date] = None
    birth_country: Optional[str] = None
    height_feet: Optional[int] = None
    height_inches: Optional[int] = None
    weight_pounds: Optional[int] = None
    college: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class PlayerTeamSeasonBase(BaseModel):
    player_id: int
    team_id: int
    season: int
    league_code: str
    jersey: Optional[int] = None
    active: bool
    pos: Optional[str] = None

class PlayerTeamSeasonOut(PlayerTeamSeasonBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class PlayerGameStatsBase(BaseModel):
    player_id: int
    game_id: int
    team_id: int
    season: Optional[int] = None
    pos: Optional[str] = None
    minutes: Optional[str] = None
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
    comment: Optional[str] = None

class PlayerGameStatsOut(PlayerGameStatsBase):
    model_config = ConfigDict(from_attributes=True)

class PlayerGameStatsResponse(BaseModel):
    game_id: int
    player_id: int
    team_id: int
    season: Optional[int] = None
    pos: Optional[str] = None
    minutes: Optional[str] = None
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
    comment: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)