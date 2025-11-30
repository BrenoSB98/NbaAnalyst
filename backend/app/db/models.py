from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    TIMESTAMP,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class Season(Base):
    __tablename__ = "seasons"

    season = Column(Integer, primary_key=True)


class League(Base):
    __tablename__ = "leagues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(Text)

    teams_info = relationship("TeamLeagueInfo", back_populates="league")


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    nickname = Column(Text)
    code = Column(String)
    city = Column(Text)
    logo = Column(Text)
    all_star = Column(Boolean, nullable=False, default=False)
    nba_franchise = Column(Boolean, nullable=False, default=False)

    leagues_info = relationship("TeamLeagueInfo", back_populates="team")
    home_games = relationship("Game", back_populates="home_team", foreign_keys="Game.home_team_id")
    away_games = relationship("Game", back_populates="away_team", foreign_keys="Game.away_team_id")
    team_season_stats = relationship("TeamSeasonStats", back_populates="team")
    game_scores = relationship("GameTeamScore", back_populates="team")
    game_stats = relationship("GameTeamStats", back_populates="team")
    player_team_seasons = relationship("PlayerTeamSeason", back_populates="team")
    player_game_stats = relationship("PlayerGameStats", back_populates="team")


class TeamLeagueInfo(Base):
    __tablename__ = "team_league_info"

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.id", ondelete="CASCADE"), nullable=False)
    conference = Column(Text)
    division = Column(Text)

    __table_args__ = (
        UniqueConstraint("team_id", "league_id", name="uq_team_league"),
    )

    team = relationship("Team", back_populates="leagues_info")
    league = relationship("League", back_populates="teams_info")


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True)
    league = Column(String)
    season = Column(Integer, ForeignKey("seasons.season"), nullable=False)
    date_start = Column(TIMESTAMP(timezone=True), nullable=False)
    date_end = Column(TIMESTAMP(timezone=True))
    duration = Column(String)
    stage = Column(Integer)
    status_short = Column(Integer)
    status_long = Column(Text)
    periods_current = Column(Integer)
    periods_total = Column(Integer)
    periods_end_of_period = Column(Boolean)
    arena_name = Column(Text)
    arena_city = Column(Text)
    arena_state = Column(Text)
    arena_country = Column(Text)
    times_tied = Column(Integer)
    lead_changes = Column(Integer)
    nugget = Column(Text)
    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)

    __table_args__ = (
        CheckConstraint("home_team_id <> away_team_id", name="chk_game_teams_different"),
    )

    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_games")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_games")
    scores = relationship("GameTeamScore", back_populates="game")
    stats = relationship("GameTeamStats", back_populates="game")
    player_game_stats = relationship("PlayerGameStats", back_populates="game")


class GameTeamScore(Base):
    __tablename__ = "game_team_scores"

    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"), primary_key=True)
    is_home = Column(Boolean, nullable=False)
    win = Column(Integer)
    loss = Column(Integer)
    series_win = Column(Integer)
    series_loss = Column(Integer)
    points = Column(Integer)
    linescore_q1 = Column(Integer)
    linescore_q2 = Column(Integer)
    linescore_q3 = Column(Integer)
    linescore_q4 = Column(Integer)

    __table_args__ = (
        UniqueConstraint("game_id", "is_home", name="uq_game_side"),
    )

    game = relationship("Game", back_populates="scores")
    team = relationship("Team", back_populates="game_scores")


class GameTeamStats(Base):
    __tablename__ = "game_team_stats"

    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"), primary_key=True)
    fast_break_points = Column(Integer)
    points_in_paint = Column(Integer)
    biggest_lead = Column(Integer)
    second_chance_points = Column(Integer)
    points_off_turnovers = Column(Integer)
    longest_run = Column(Integer)
    points = Column(Integer)
    fgm = Column(Integer)
    fga = Column(Integer)
    fgp = Column(Numeric(5, 2))
    ftm = Column(Integer)
    fta = Column(Integer)
    ftp = Column(Numeric(5, 2))
    tpm = Column(Integer)
    tpa = Column(Integer)
    tpp = Column(Numeric(5, 2))
    off_reb = Column(Integer)
    def_reb = Column(Integer)
    tot_reb = Column(Integer)
    assists = Column(Integer)
    p_fouls = Column(Integer)
    steals = Column(Integer)
    turnovers = Column(Integer)
    blocks = Column(Integer)
    plus_minus = Column(Integer)
    minutes = Column(String)

    game = relationship("Game", back_populates="stats")
    team = relationship("Team", back_populates="game_stats")


class TeamSeasonStats(Base):
    __tablename__ = "team_season_stats"

    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True)
    season = Column(Integer, ForeignKey("seasons.season"), primary_key=True)
    games = Column(Integer)
    fast_break_points = Column(Integer)
    points_in_paint = Column(Integer)
    biggest_lead = Column(Integer)
    second_chance_points = Column(Integer)
    points_off_turnovers = Column(Integer)
    longest_run = Column(Integer)
    points = Column(Integer)
    fgm = Column(Integer)
    fga = Column(Integer)
    fgp = Column(Numeric(5, 2))
    ftm = Column(Integer)
    fta = Column(Integer)
    ftp = Column(Numeric(5, 2))
    tpm = Column(Integer)
    tpa = Column(Integer)
    tpp = Column(Numeric(5, 2))
    off_reb = Column(Integer)
    def_reb = Column(Integer)
    tot_reb = Column(Integer)
    assists = Column(Integer)
    p_fouls = Column(Integer)
    steals = Column(Integer)
    turnovers = Column(Integer)
    blocks = Column(Integer)
    plus_minus = Column(Integer)

    team = relationship("Team", back_populates="team_season_stats")


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    firstname = Column(Text, nullable=False)
    lastname = Column(Text, nullable=False)
    birth_date = Column(Date)
    birth_country = Column(Text)
    nba_start = Column(Integer)
    nba_pro = Column(Integer)
    height_feet = Column(Integer)
    height_inches = Column(Integer)
    height_meters = Column(Numeric(4, 2))
    weight_pounds = Column(Integer)
    weight_kilograms = Column(Numeric(5, 2))
    college = Column(Text)
    affiliation = Column(Text)

    team_seasons = relationship("PlayerTeamSeason", back_populates="player")
    game_stats = relationship("PlayerGameStats", back_populates="player")


class PlayerTeamSeason(Base):
    __tablename__ = "player_team_season"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    season = Column(Integer, ForeignKey("seasons.season"), nullable=False)
    league_code = Column(String, nullable=False)
    jersey = Column(Integer)
    active = Column(Boolean, nullable=False)
    pos = Column(String)

    __table_args__ = (
        UniqueConstraint("player_id", "team_id", "season", "league_code", name="uq_player_team_season_league"),
    )

    player = relationship("Player", back_populates="team_seasons")
    team = relationship("Team", back_populates="player_team_seasons")
    season_rel = relationship("Season")


class PlayerGameStats(Base):
    __tablename__ = "player_game_stats"

    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    season = Column(Integer, ForeignKey("seasons.season"))
    pos = Column(String)
    minutes = Column(String)
    points = Column(Integer)
    fgm = Column(Integer)
    fga = Column(Integer)
    fgp = Column(Numeric(5, 2))
    ftm = Column(Integer)
    fta = Column(Integer)
    ftp = Column(Numeric(5, 2))
    tpm = Column(Integer)
    tpa = Column(Integer)
    tpp = Column(Numeric(5, 2))
    off_reb = Column(Integer)
    def_reb = Column(Integer)
    tot_reb = Column(Integer)
    assists = Column(Integer)
    p_fouls = Column(Integer)
    steals = Column(Integer)
    turnovers = Column(Integer)
    blocks = Column(Integer)
    plus_minus = Column(Integer)
    comment = Column(Text)

    player = relationship("Player", back_populates="game_stats")
    game = relationship("Game", back_populates="player_game_stats")
    team = relationship("Team", back_populates="player_game_stats")
    season_rel = relationship("Season")
