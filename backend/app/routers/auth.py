from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.auth import hash_password, verify_password, create_access_token, decode_access_token
from app.config import config
from app.db.db_utils import get_db
from app.db.models import Team, User
from app.schemas.auth import Token, UserCreate, UserResponse, UserUpdateTimeFavorito

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/autenticacao/login")
_token_blacklist: set = set()

def obter_usuario_atual(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if token in _token_blacklist:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")

    email = decode_access_token(token)
    if email is None:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")

    usuario = db.query(User).filter(User.email == email).first()
    if usuario is None:
        raise HTTPException(status_code=401, detail="Usuário não encontrado.")

    if not usuario.is_active:
        raise HTTPException(status_code=403, detail="Usuário inativo.")
    return usuario

def obter_usuario_admin(usuario_atual: User = Depends(obter_usuario_atual)):
    if usuario_atual.role != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores.")
    return usuario_atual

@router.post("/registrar", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def registrar_usuario(dados: UserCreate, db: Session = Depends(get_db)):
    usuario_existente = db.query(User).filter(User.email == dados.email).first()
    if usuario_existente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="E-mail já cadastrado.")

    if dados.favorite_team_id is not None:
        time_existe = db.query(Team).filter(Team.id == dados.favorite_team_id).first()
        if not time_existe:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Time favorito não encontrado.")

    novo_usuario = User(
        email=dados.email,
        full_name=dados.full_name,
        birth_date=dados.birth_date,
        favorite_team_id=dados.favorite_team_id,
        hashed_password=hash_password(dados.password),
        is_active=True,
        role="user",
        created_at=datetime.now(timezone.utc),
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = db.query(User).filter(User.email == form_data.username).first()

    if not usuario:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha inválidos.")

    if not verify_password(form_data.password, usuario.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha inválidos.")

    if not usuario.is_active:
        raise HTTPException(status_code=403, detail="Usuário inativo.")

    token = create_access_token(data={"sub": usuario.email},expires_delta=timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": token, "token_type": "bearer"}

@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(token: str = Depends(oauth2_scheme)):
    _token_blacklist.add(token)
    return {"message": "Logout realizado com sucesso."}

@router.get("/eu", response_model=UserResponse)
def meu_perfil(usuario_atual: User = Depends(obter_usuario_atual)):
    return usuario_atual

@router.patch("/eu/time-favorito", response_model=UserResponse)
def atualizar_time_favorito(dados: UserUpdateTimeFavorito, db: Session = Depends(get_db), usuario_atual: User = Depends(obter_usuario_atual)):
    if dados.favorite_team_id is not None:
        time_existe = db.query(Team).filter(Team.id == dados.favorite_team_id).first()
        if not time_existe:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Time favorito não encontrado.")
 
    usuario_atual.favorite_team_id = dados.favorite_team_id
    db.commit()
    db.refresh(usuario_atual)
    return usuario_atual