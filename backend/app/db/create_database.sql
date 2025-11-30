-- 1) Seasons
CREATE TABLE seasons (
    season INT PRIMARY KEY
);

-- 2) Leagues
CREATE TABLE leagues (
    id SERIAL PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    description TEXT
);

-- 3) Teams
CREATE TABLE teams (
    id INT PRIMARY KEY,
    name TEXT NOT NULL,
    nickname TEXT,
    code TEXT,
    city TEXT,
    logo TEXT,
    all_star BOOLEAN NOT NULL DEFAULT FALSE,
    nba_franchise BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_teams_code ON teams(code);
CREATE INDEX idx_teams_name ON teams(name);

-- 4) Team-League Info
CREATE TABLE team_league_info (
    id SERIAL PRIMARY KEY,
    team_id INT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    league_id INT NOT NULL REFERENCES leagues(id) ON DELETE CASCADE,
    conference TEXT,
    division TEXT,
    CONSTRAINT uq_team_league UNIQUE (team_id, league_id)
);

-- 5) Games
CREATE TABLE games (
    id INT PRIMARY KEY,
    league TEXT,
    season INT NOT NULL REFERENCES seasons(season),
    date_start TIMESTAMPTZ NOT NULL,
    date_end TIMESTAMPTZ,
    duration INTERVAL,
    stage INT,
    status_short INT,
    status_long TEXT,
    periods_current INT,
    periods_total INT,
    periods_end_of_period BOOLEAN,
    arena_name TEXT,
    arena_city TEXT,
    arena_state TEXT,
    arena_country TEXT,
    times_tied INT,
    lead_changes INT,
    nugget TEXT,
    home_team_id INT NOT NULL REFERENCES teams(id),
    away_team_id INT NOT NULL REFERENCES teams(id),
    CONSTRAINT chk_game_teams_different CHECK (home_team_id <> away_team_id)
);

CREATE INDEX idx_games_season ON games(season);
CREATE INDEX idx_games_date_start ON games(date_start);

-- 6) Game Team Scores
CREATE TABLE game_team_scores (
    game_id INT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    team_id INT NOT NULL REFERENCES teams(id),
    is_home BOOLEAN NOT NULL,
    win INT,
    loss INT,
    series_win INT,
    series_loss INT,
    points INT,
    linescore_q1 INT,
    linescore_q2 INT,
    linescore_q3 INT,
    linescore_q4 INT,
    PRIMARY KEY (game_id, team_id),
    CONSTRAINT uq_game_side UNIQUE (game_id, is_home)
);

-- 7) Game Team Stats (games/statistics)
CREATE TABLE game_team_stats (
    game_id INT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    team_id INT NOT NULL REFERENCES teams(id),
    fast_break_points INT,
    points_in_paint INT,
    biggest_lead INT,
    second_chance_points INT,
    points_off_turnovers INT,
    longest_run INT,
    points INT,
    fgm INT,
    fga INT,
    fgp NUMERIC(5,2),
    ftm INT,
    fta INT,
    ftp NUMERIC(5,2),
    tpm INT,
    tpa INT,
    tpp NUMERIC(5,2),
    off_reb INT,
    def_reb INT,
    tot_reb INT,
    assists INT,
    p_fouls INT,
    steals INT,
    turnovers INT,
    blocks INT,
    plus_minus INT,
    minutes TEXT,
    PRIMARY KEY (game_id, team_id)
);

-- 8) Team Season Stats (teams/statistics)
CREATE TABLE team_season_stats (
    team_id INT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    season INT NOT NULL REFERENCES seasons(season),
    games INT,
    fast_break_points INT,
    points_in_paint INT,
    biggest_lead INT,
    second_chance_points INT,
    points_off_turnovers INT,
    longest_run INT,
    points INT,
    fgm INT,
    fga INT,
    fgp NUMERIC(5,2),
    ftm INT,
    fta INT,
    ftp NUMERIC(5,2),
    tpm INT,
    tpa INT,
    tpp NUMERIC(5,2),
    off_reb INT,
    def_reb INT,
    tot_reb INT,
    assists INT,
    p_fouls INT,
    steals INT,
    turnovers INT,
    blocks INT,
    plus_minus INT,
    PRIMARY KEY (team_id, season)
);

CREATE INDEX idx_team_season_stats_season ON team_season_stats(season);

-- 9) Players
CREATE TABLE players (
    id INT PRIMARY KEY,
    firstname TEXT NOT NULL,
    lastname TEXT NOT NULL,
    birth_date DATE,
    birth_country TEXT,
    nba_start INT,
    nba_pro INT,
    height_feet INT,
    height_inches INT,
    height_meters NUMERIC(4,2),
    weight_pounds INT,
    weight_kilograms NUMERIC(5,2),
    college TEXT,
    affiliation TEXT
);

CREATE INDEX idx_players_name ON players(lastname, firstname);

-- 10) Player-Team-Season (rosters)
CREATE TABLE player_team_season (
    id SERIAL PRIMARY KEY,
    player_id INT NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    team_id INT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    season INT NOT NULL REFERENCES seasons(season),
    league_code TEXT NOT NULL,
    jersey INT,
    active BOOLEAN NOT NULL,
    pos TEXT,
    CONSTRAINT uq_player_team_season_league UNIQUE (player_id, team_id, season, league_code)
);

CREATE INDEX idx_pts_team_season ON player_team_season(team_id, season);
CREATE INDEX idx_pts_player_season ON player_team_season(player_id, season);

-- 11) Player Game Stats (players/statistics)
CREATE TABLE player_game_stats (
    player_id INT NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    team_id INT NOT NULL REFERENCES teams(id),
    game_id INT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    season INT REFERENCES seasons(season),
    pos TEXT,
    minutes TEXT,
    points INT,
    fgm INT,
    fga INT,
    fgp NUMERIC(5,2),
    ftm INT,
    fta INT,
    ftp NUMERIC(5,2),
    tpm INT,
    tpa INT,
    tpp NUMERIC(5,2),
    off_reb INT,
    def_reb INT,
    tot_reb INT,
    assists INT,
    p_fouls INT,
    steals INT,
    turnovers INT,
    blocks INT,
    plus_minus INT,
    comment TEXT,
    PRIMARY KEY (player_id, game_id)
);

CREATE INDEX idx_pgs_game ON player_game_stats(game_id);
CREATE INDEX idx_pgs_team_game ON player_game_stats(team_id, game_id);
CREATE INDEX idx_pgs_player_season ON player_game_stats(player_id, season);