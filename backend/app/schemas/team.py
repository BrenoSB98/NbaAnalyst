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

class TeamListItem(BaseModel):
    id: int
    nome: str
    apelido: Optional[str] = None
    codigo: Optional[str] = None
    cidade: Optional[str] = None
    logo: Optional[str] = None
    nba_franchise: bool
    all_star: bool

    model_config = ConfigDict(from_attributes=True)

class TeamListResponse(BaseModel):
    total: int
    pagina: int
    tamanho_pagina: int
    times: List[TeamListItem]

class InfoLiga(BaseModel):
    liga: Optional[str] = None
    conferencia: Optional[str] = None
    divisao: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class TeamDetalheResponse(BaseModel):
    id: int
    nome: str
    apelido: Optional[str] = None
    codigo: Optional[str] = None
    cidade: Optional[str] = None
    logo: Optional[str] = None
    all_star: bool
    nba_franchise: bool
    info_liga: Optional[InfoLiga] = None

    model_config = ConfigDict(from_attributes=True)

class EstatisticasTimeResponse(BaseModel):
    time_id: int
    nome_time: str
    temporada: int
    total_jogos: int
    jogos_casa: int
    jogos_fora: int
    total_jogadores: int
    vitorias: int
    derrotas: int
    aproveitamento: float

class UltimoJogoPerformance(BaseModel):
    jogo_id: int
    data: Optional[object] = None
    adversario_id: int
    em_casa: bool
    pontos_feitos: int
    pontos_sofridos: int
    resultado: str

class PerformanceTimeResponse(BaseModel):
    time_id: int
    nome_time: str
    temporada: int
    total_jogos: int
    vitorias: int
    derrotas: int
    aproveitamento: float
    record_casa: str
    record_fora: str
    media_pontos_feitos: float
    media_pontos_sofridos: float
    diferencial_pontos: float
    ultimos_5_jogos: List[UltimoJogoPerformance]
    mensagem: Optional[str] = None

class TimeComparacao(BaseModel):
    id: int
    nome: str
    vitorias: int
    derrotas: int
    aproveitamento: float

class ConfrontoDireto(BaseModel):
    total_jogos: int
    vitorias_time1: int
    vitorias_time2: int

class ComparacaoTimesResponse(BaseModel):
    temporada: int
    time1: TimeComparacao
    time2: TimeComparacao
    confronto_direto: ConfrontoDireto

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