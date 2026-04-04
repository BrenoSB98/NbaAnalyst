from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    birth_date: date
    favorite_team_id: Optional[int] = None
    password: str

    @field_validator("password")
    def senha_minima(cls, v):
        if len(v) < 6:
            raise ValueError("A senha deve ter no mínimo 6 caracteres.")
        return v

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    birth_date: date
    favorite_team_id: Optional[int] = None
    is_active: bool
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    
class UserUpdateTimeFavorito(BaseModel):
    favorite_team_id: Optional[int] = None

class UserUpdateSenha(BaseModel):
    senha_atual: str
    nova_senha: str

    @field_validator("nova_senha")
    def nova_senha_minima(cls, v):
        if len(v) < 6:
            raise ValueError("A nova senha deve ter no mínimo 6 caracteres.")
        return v