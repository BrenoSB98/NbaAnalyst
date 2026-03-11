from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict

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

    model_config = ConfigDict(from_attributes=True)

class GameListItem(BaseModel):
    id: int
    temporada: Optional[int] = None
    liga: Optional[str] = None
    data_inicio: Optional[datetime] = None
    status_short: Optional[int] = None
    status_long: Optional[str] = None
    time_casa_id: Optional[int] = None
    time_fora_id: Optional[int] = None
    pontos_casa: Optional[int] = None
    pontos_fora: Optional[int] = None
    arena: Optional[str] = None
    cidade: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class GameListResponse(BaseModel):
    total: int
    pagina: int
    tamanho_pagina: int
    jogos: List[GameListItem]

class TimeResumo(BaseModel):
    id: int
    nome: Optional[str] = None

class ProximoJogoItem(BaseModel):
    id: int
    data_inicio: Optional[datetime] = None
    time_casa: TimeResumo
    time_fora: TimeResumo
    arena: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ProximosJogosResponse(BaseModel):
    total: int
    dias: int
    jogos: List[ProximoJogoItem]

class ArenaInfo(BaseModel):
    nome: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    pais: Optional[str] = None

class ParciaisJogo(BaseModel):
    q1: Optional[int] = None
    q2: Optional[int] = None
    q3: Optional[int] = None
    q4: Optional[int] = None

class TimeJogoDetalhe(BaseModel):
    id: int
    nome: Optional[str] = None
    apelido: Optional[str] = None
    logo: Optional[str] = None
    pontos: Optional[int] = None
    parciais: Optional[ParciaisJogo] = None

class GameDetalheResponse(BaseModel):
    id: int
    temporada: Optional[int] = None
    liga: Optional[str] = None
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None
    duracao: Optional[str] = None
    status_short: Optional[int] = None
    status_long: Optional[str] = None
    fase: Optional[int] = None
    periodos_atual: Optional[int] = None
    periodos_total: Optional[int] = None
    arena: ArenaInfo
    time_casa: TimeJogoDetalhe
    time_fora: TimeJogoDetalhe
    empates: Optional[int] = None
    mudancas_lideranca: Optional[int] = None
    nugget: Optional[str] = None

class GameTeamStatsItem(BaseModel):
    time_id: int
    nome_time: Optional[str] = None
    pontos: Optional[int] = None
    fgm: Optional[int] = None
    fga: Optional[int] = None
    fgp: Optional[float] = None
    ftm: Optional[int] = None
    fta: Optional[int] = None
    ftp: Optional[float] = None
    tpm: Optional[int] = None
    tpa: Optional[int] = None
    tpp: Optional[float] = None
    rebotes_ofensivos: Optional[int] = None
    rebotes_defensivos: Optional[int] = None
    rebotes_totais: Optional[int] = None
    assistencias: Optional[int] = None
    roubos: Optional[int] = None
    bloqueios: Optional[int] = None
    turnovers: Optional[int] = None
    faltas: Optional[int] = None
    plus_minus: Optional[int] = None
    fast_break_points: Optional[int] = None
    pontos_no_garrafao: Optional[int] = None
    segundas_chances: Optional[int] = None
    pontos_apos_turnover: Optional[int] = None
    maior_vantagem: Optional[int] = None
    maior_sequencia: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class EstatisticasTimesJogoResponse(BaseModel):
    jogo_id: int
    estatisticas_times: List[GameTeamStatsItem]

class PlayerStatsJogoItem(BaseModel):
    jogador_id: int
    nome_jogador: str
    time_id: int
    posicao: Optional[str] = None
    minutos: Optional[str] = None
    pontos: Optional[int] = None
    assistencias: Optional[int] = None
    rebotes_totais: Optional[int] = None
    rebotes_ofensivos: Optional[int] = None
    rebotes_defensivos: Optional[int] = None
    roubos: Optional[int] = None
    bloqueios: Optional[int] = None
    turnovers: Optional[int] = None
    faltas: Optional[int] = None
    fgm: Optional[int] = None
    fga: Optional[int] = None
    fgp: Optional[float] = None
    ftm: Optional[int] = None
    fta: Optional[int] = None
    ftp: Optional[float] = None
    tpm: Optional[int] = None
    tpa: Optional[int] = None
    tpp: Optional[float] = None
    plus_minus: Optional[int] = None
    comentario: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class EstatisticasJogadoresJogoResponse(BaseModel):
    jogo_id: int
    total: int
    estatisticas: List[PlayerStatsJogoItem]

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
    model_config = ConfigDict(from_attributes=True)