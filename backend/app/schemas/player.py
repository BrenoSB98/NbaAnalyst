from datetime import date, datetime
from typing import Optional, List

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

class PlayerListItem(BaseModel):
    id: int
    nome: Optional[str] = None
    sobrenome: Optional[str] = None
    data_nascimento: Optional[date] = None
    pais_nascimento: Optional[str] = None
    inicio_nba: Optional[int] = None
    altura_metros: Optional[float] = None
    peso_kg: Optional[float] = None
    faculdade: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class PlayerListResponse(BaseModel):
    total: int
    pagina: int
    tamanho_pagina: int
    jogadores: List[PlayerListItem]

class HistoricoTimeItem(BaseModel):
    temporada: int
    time_id: int
    nome_time: str
    camisa: Optional[int] = None
    posicao: Optional[str] = None
    ativo: bool

    model_config = ConfigDict(from_attributes=True)

class PlayerDetalheResponse(BaseModel):
    id: int
    nome: Optional[str] = None
    sobrenome: Optional[str] = None
    data_nascimento: Optional[date] = None
    pais_nascimento: Optional[str] = None
    inicio_nba: Optional[int] = None
    altura_pes: Optional[int] = None
    altura_polegadas: Optional[int] = None
    altura_metros: Optional[float] = None
    peso_libras: Optional[int] = None
    peso_kg: Optional[float] = None
    faculdade: Optional[str] = None
    afiliacao: Optional[str] = None
    historico_times: List[HistoricoTimeItem]

    model_config = ConfigDict(from_attributes=True)

class ElencoJogadorItem(BaseModel):
    id: int
    nome: str
    camisa: Optional[int] = None
    posicao: Optional[str] = None
    ativo: bool
    altura_metros: Optional[float] = None
    peso_kg: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class ElencoTimeResponse(BaseModel):
    time_id: int
    nome_time: str
    temporada: int
    total: int
    jogadores: List[ElencoJogadorItem]

class TotaisTemporada(BaseModel):
    pontos: int
    assistencias: int
    rebotes: int
    roubos: int
    bloqueios: int
    turnovers: int

class MediasTemporada(BaseModel):
    pontos: float
    assistencias: float
    rebotes: float
    roubos: float
    bloqueios: float
    turnovers: float
    fg_pct: float
    three_pct: float
    ft_pct: float

class EstatisticasTemporadaResponse(BaseModel):
    jogador_id: int
    nome_jogador: str
    temporada: int
    jogos_disputados: Optional[int] = None
    totais: Optional[TotaisTemporada] = None
    medias: Optional[MediasTemporada] = None
    mensagem: Optional[str] = None

class JogoStatItem(BaseModel):
    jogo_id: int
    data: Optional[datetime] = None
    temporada: Optional[int] = None
    adversario_id: Optional[int] = None
    minutos: Optional[str] = None
    pontos: Optional[int] = None
    assistencias: Optional[int] = None
    rebotes: Optional[int] = None
    roubos: Optional[int] = None
    bloqueios: Optional[int] = None
    turnovers: Optional[int] = None
    fg_pct: Optional[float] = None
    three_pct: Optional[float] = None
    ft_pct: Optional[float] = None
    plus_minus: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class EstatisticasJogosResponse(BaseModel):
    jogador_id: int
    nome_jogador: str
    total: int
    jogos: List[JogoStatItem]

class JogoResumoItem(BaseModel):
    jogo_id: int
    data: Optional[datetime] = None
    pontos: Optional[int] = None
    assistencias: Optional[int] = None
    rebotes: Optional[int] = None

class MediasUltimosJogos(BaseModel):
    pontos: float
    assistencias: float
    rebotes: float
    roubos: float
    bloqueios: float
    turnovers: float
    fg_pct: float
    three_pct: float
    ft_pct: float

class EstatisticasUltimosJogosResponse(BaseModel):
    jogador_id: int
    nome_jogador: str
    n_jogos: int
    jogos_analisados: int
    temporada: Optional[int] = None
    medias: Optional[MediasUltimosJogos] = None
    jogos: List[JogoResumoItem]
    mensagem: Optional[str] = None

class MediasCasaFora(BaseModel):
    pontos: float
    assistencias: float
    rebotes: float
    roubos: float
    bloqueios: float
    turnovers: float
    fg_pct: float
    three_pct: float
    ft_pct: float

class EstatisticasCasaForaResponse(BaseModel):
    jogador_id: int
    nome_jogador: str
    temporada: int
    local: str
    jogos_disputados: Optional[int] = None
    medias: Optional[MediasCasaFora] = None
    jogos: Optional[List[JogoResumoItem]] = None
    mensagem: Optional[str] = None

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