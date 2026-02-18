from typing import Optional
from pydantic import BaseModel, Field

class LeagueInfoResponse(BaseModel):
    league_code: Optional[str] = Field(None, description="Código da liga")
    conference: Optional[str] = Field(None, description="Conferência do time")
    division: Optional[str] = Field(None, description="Divisão do time")

    class Config:
        from_attributes = True


class TeamResponse(BaseModel):
    id: int = Field(..., description="ID único do time")
    name: str = Field(..., description="Nome completo do time")
    nickname: Optional[str] = Field(None, description="Apelido do time")
    code: Optional[str] = Field(None, description="Código de 3 letras do time")
    city: Optional[str] = Field(None, description="Cidade do time")
    logo: Optional[str] = Field(None, description="URL do logo do time")
    all_star: Optional[bool] = Field(False, description="Se é time All-Star")
    nba_franchise: Optional[bool] = Field(True, description="Se é franquia NBA")

    class Config:
        from_attributes = True


class TeamDetailResponse(TeamResponse):
    league_info: Optional[LeagueInfoResponse] = Field(None, description="Informações de liga")

    class Config:
        from_attributes = True


class TeamListResponse(BaseModel):
    total: int = Field(..., description="Total de times encontrados")
    page: int = Field(..., description="Página atual")
    page_size: int = Field(..., description="Tamanho da página")
    teams: list[TeamResponse] = Field(..., description="Lista de times")

    class Config:
        from_attributes = True