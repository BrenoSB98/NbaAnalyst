from datetime import datetime, timedelta, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.auth import hash_password, verify_password, create_access_token, decode_access_token
from app.config import config
from app.db.db_utils import get_db
from app.db.models import Team, User
from app.schemas.auth import Token, UserCreate, UserResponse, UserUpdateTimeFavorito, UserUpdateSenha
from app.services.email_service import enviar_email_confirmacao, enviar_email_reset_senha

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

    token_confirmacao = str(uuid.uuid4())

    novo_usuario = User(
        email=dados.email,
        full_name=dados.full_name,
        birth_date=dados.birth_date,
        favorite_team_id=dados.favorite_team_id,
        hashed_password=hash_password(dados.password),
        is_active=False,
        email_confirmed=False,
        confirmation_token=token_confirmacao,
        role="user",
        created_at=datetime.now(timezone.utc),
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    try:
        enviar_email_confirmacao(
            destinatario=dados.email,
            nome=dados.full_name,
            token=token_confirmacao,
        )
    except Exception:
        pass

    return novo_usuario

@router.get("/confirmacao_conta/{token}", status_code=status.HTTP_200_OK)
def confirmar_email(token: str, db: Session = Depends(get_db)):
    usuario = db.query(User).filter(User.confirmation_token == token).first()

    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token de confirmação inválido ou já utilizado.")

    if usuario.email_confirmed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="E-mail já confirmado.")

    usuario.is_active = True
    usuario.email_confirmed = True
    usuario.confirmation_token = None
    db.commit()

    return {"message": "E-mail confirmado com sucesso. Sua conta está ativa."}

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = db.query(User).filter(User.email == form_data.username).first()

    if not usuario:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha inválidos.")

    if not verify_password(form_data.password, usuario.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha inválidos.")

    if not usuario.is_active:
        raise HTTPException(status_code=403, detail="Conta não confirmada. Verifique seu e-mail e clique no link de ativação.")

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

@router.patch("/eu/senha", status_code=status.HTTP_200_OK)
def alterar_senha(dados: UserUpdateSenha, db: Session = Depends(get_db), usuario_atual: User = Depends(obter_usuario_atual)):
    senha_correta = verify_password(dados.senha_atual, usuario_atual.hashed_password)

    if not senha_correta:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Senha atual incorreta.")

    if dados.nova_senha == dados.senha_atual:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A nova senha deve ser diferente da senha atual.")

    usuario_atual.hashed_password = hash_password(dados.nova_senha)
    db.commit()
    return {"message": "Senha alterada com sucesso."}

@router.post("/solicitar-reset-senha", status_code=status.HTTP_200_OK)
def solicitar_reset_senha(dados: dict, db: Session = Depends(get_db)):
    email = dados.get("email", "").strip()

    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Informe o e-mail.")

    usuario = db.query(User).filter(User.email == email).first()

    if not usuario:
        return {"message": "Se o e-mail estiver cadastrado, você receberá as instruções em breve."}

    token_reset = str(uuid.uuid4())
    expiracao = datetime.now(timezone.utc) + timedelta(hours=1)

    usuario.reset_token = token_reset
    usuario.reset_token_expira = expiracao
    db.commit()

    try:
        enviar_email_reset_senha(
            destinatario=usuario.email,
            nome=usuario.full_name,
            token=token_reset,
        )
    except Exception:
        pass

    return {"message": "Se o e-mail estiver cadastrado, você receberá as instruções em breve."}


@router.post("/redefinir-senha", status_code=status.HTTP_200_OK)
def redefinir_senha(dados: dict, db: Session = Depends(get_db)):
    token = dados.get("token", "").strip()
    nova_senha = dados.get("nova_senha", "").strip()

    if not token or not nova_senha:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token e nova senha são obrigatórios.")

    if len(nova_senha) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A nova senha deve ter no mínimo 6 caracteres.")

    usuario = db.query(User).filter(User.reset_token == token).first()

    if not usuario:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido ou já utilizado.")

    agora = datetime.now(timezone.utc)
    expiracao = usuario.reset_token_expira

    if expiracao is None or agora > expiracao:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O link de redefinição expirou. Solicite um novo.")

    usuario.hashed_password = hash_password(nova_senha)
    usuario.reset_token = None
    usuario.reset_token_expira = None
    db.commit()

    return {"message": "Senha redefinida com sucesso. Faça login com a nova senha."}