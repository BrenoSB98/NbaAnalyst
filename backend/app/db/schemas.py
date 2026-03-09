from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

class SeasonBase(BaseModel):
    season: int

class SeasonOut(SeasonBase):
    model_config = ConfigDict(
        from_attributes=True
    )

class LeagueBase(BaseModel):
    code: str
    description: Optional[str] = None

class LeagueOut(LeagueBase):
    id: int
    
    model_config = ConfigDict(
        from_attributes=True
    )

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
    
    model_config = ConfigDict(
        from_attributes=True
    )

class TeamLeagueInfoBase(BaseModel):
    team_id: int
    league_id: int
    conference: Optional[str] = None
    division: Optional[str] = None

class TeamLeagueInfoOut(TeamLeagueInfoBase):
    id: int
    
    model_config = ConfigDict(
        from_attributes=True
    )

class GameBase(BaseModel):
    league: Optional[str] = None
    season: int
    date_start: datetime
    date_end: Optional[datetime] = None
    duration: Optional[str] = None
    stage: Optional[int] = None
    status_short: Optional[int] = None
    status_long: Optional[str] = None
    periods_current: Optional[int] = None
    periods_total: Optional[int] = None
    periods_end_of_period: Optional[bool] = None
    arena_name: Optional[str] = None
    arena_city: Optional[str] = None
    arena_state: Optional[str] = None
    arena_country: Optional[str] = None
    times_tied: Optional[int] = None
    lead_changes: Optional[int] = None
    nugget: Optional[str] = None
    home_team_id: int
    away_team_id: int

class GameOut(GameBase):
    id: int
    
    model_config = ConfigDict(
        from_attributes=True)

class GameResponse(BaseModel):
    id: int
    league: Optional[str] = None
    season: Optional[int] = None
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    status_short: Optional[int] = None
    status_long: Optional[str] = None
    arena_name: Optional[str] = None
    arena_city: Optional[str] = None
    home_team_id: Optional[int] = None
    away_team_id: Optional[int] = None
    
    model_config = ConfigDict(
        from_attributes=True
    )

class GameTeamScoreBase(BaseModel):
    game_id: int
    team_id: int
    is_home: bool
    win: Optional[int] = None
    loss: Optional[int] = None
    series_win: Optional[int] = None
    series_loss: Optional[int] = None
    points: Optional[int] = None
    linescore_q1: Optional[int] = None
    linescore_q2: Optional[int] = None
    linescore_q3: Optional[int] = None
    linescore_q4: Optional[int] = None

class GameTeamScoreOut(GameTeamScoreBase):
    model_config = ConfigDict(
        from_attributes=True
    )

class GameTeamScoreResponse(BaseModel):
    game_id: int
    team_id: int
    is_home: Optional[bool] = None
    win: Optional[int] = None
    loss: Optional[int] = None
    series_win: Optional[int] = None
    series_loss: Optional[int] = None
    points: Optional[int] = None
    linescore_q1: Optional[int] = None
    linescore_q2: Optional[int] = None
    linescore_q3: Optional[int] = None
    linescore_q4: Optional[int] = None
    
    model_config = ConfigDict(
        from_attributes=True
    )

class GameTeamStatsBase(BaseModel):
    game_id: int
    team_id: int
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
    minutes: Optional[str] = None

class GameTeamStatsOut(GameTeamStatsBase):
    model_config = ConfigDict(
        from_attributes=True
    )

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
    model_config = ConfigDict(
        from_attributes=True
    )

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
    
    model_config = ConfigDict(
        from_attributes=True
    )

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
    
    model_config = ConfigDict(
        from_attributes=True
    )

class TeamResponse(BaseModel):
    id: int
    name: Optional[str] = None
    nickname: Optional[str] = None
    code: Optional[str] = None
    city: Optional[str] = None
    logo: Optional[str] = None
    
    model_config = ConfigDict(
        from_attributes=True
    )

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
    
    model_config = ConfigDict(
        from_attributes=True
    )

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
    model_config = ConfigDict(
        from_attributes=True
    )

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
    
    model_config = ConfigDict(
        from_attributes=True
    )
    
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    birth_date: date
    favorite_team_id: Optional[int] = None
    password: str
    confirm_password: str

    @field_validator("confirm_password")
    def senhas_devem_ser_iguais(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("As senhas não coincidem.")
        return v
class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    birth_date: date
    favorite_team_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class TeamAvgPointsResponse(BaseModel):
    team_id: int
    team_name: str
    season: int
    total_games: int
    avg_points: float
    avg_points_conceded: float

class PlayerAvgStatsResponse(BaseModel):
    player_id: int
    player_name: str
    season: int
    total_games: int
    avg_points: float
    avg_assists: float
    avg_rebounds: float
    avg_steals: float
    avg_blocks: float

class TeamLastGamesResponse(BaseModel):
    team_id: int
    team_name: str
    game_id: int
    date: Optional[datetime]
    opponent: str
    points_scored: Optional[int]
    points_conceded: Optional[int]
    win: Optional[bool]

class ResultadoJogo(BaseModel):
    game_id: int
    data: Optional[datetime] = None
    real: float
    predicao: float
    erro_absoluto: float
class BacktestMetrics(BaseModel):
    jogador_id: int
    nome_jogador: str
    temporada: int
    estatistica: str
    total_testes: int
    erro_medio_absoluto: Optional[float] = None
    resultados_detalhados: list[ResultadoJogo]
    
class MediasJogador(BaseModel):
    pontos: Optional[float] = None
    assistencias: Optional[float] = None
    rebotes: Optional[float] = None
    roubos: Optional[float] = None
    bloqueios: Optional[float] = None
    turnovers: Optional[float] = None
    fg_pct: Optional[float] = None
    three_pct: Optional[float] = None
    ft_pct: Optional[float] = None

class AnalyticsSummary(BaseModel):
    jogador_id: int
    nome_jogador: str
    temporada: int
    jogos_analisados: int
    medias: MediasJogador
