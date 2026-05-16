import sys
import os
from datetime import date, datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

DATABASE_URL_TEST = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def engine():
    from app.db.base import Base
    motor = create_engine(DATABASE_URL_TEST, connect_args={"check_same_thread": False})

    @event.listens_for(motor, "connect")
    def ativar_fk(conn, record):
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    with patch("app.db.session.create_engine") as mock_engine:
        mock_engine.return_value = motor
        Base.metadata.create_all(bind=motor)

    yield motor
    Base.metadata.drop_all(bind=motor)


@pytest.fixture(scope="function")
def db(engine):
    from app.db.base import Base
    SessionLocal = sessionmaker(bind=engine)
    connection = engine.connect()
    transacao = connection.begin()
    session = SessionLocal(bind=connection)
    yield session
    session.close()
    transacao.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db):
    with patch("app.db.session.create_engine"):
        with patch("app.db.session.SessionLocal"):
            from app.main import app
            from app.db.db_utils import get_db
            from fastapi.testclient import TestClient

            def substituir_get_db():
                yield db

            app.dependency_overrides[get_db] = substituir_get_db
            with TestClient(app, raise_server_exceptions=False) as c:
                yield c
            app.dependency_overrides.clear()


# ── Fixtures de dados ──────────────────────────────────────────────────────────

@pytest.fixture
def temporada(db):
    from app.db.models import Season
    s = Season(season=2025)
    db.add(s)
    db.commit()
    return s


@pytest.fixture
def time_lakers(db):
    from app.db.models import Team
    t = Team(id=1, name="Los Angeles Lakers", nickname="Lakers", code="LAL", city="Los Angeles", logo="https://logo.url/lal.png", all_star=False, nba_franchise=True)
    db.add(t)
    db.commit()
    return t


@pytest.fixture
def time_celtics(db):
    from app.db.models import Team
    t = Team(id=2, name="Boston Celtics", nickname="Celtics", code="BOS", city="Boston", logo="https://logo.url/bos.png", all_star=False, nba_franchise=True)
    db.add(t)
    db.commit()
    return t


@pytest.fixture
def liga(db):
    from app.db.models import League
    lg = League(code="standard", description="NBA Standard")
    db.add(lg)
    db.commit()
    return lg


@pytest.fixture
def jogo(db, temporada, time_lakers, time_celtics):
    from app.db.models import Game
    g = Game(
        id=1001,
        league="standard",
        season=2025,
        date_start=datetime(2025, 1, 15, 20, 0, tzinfo=timezone.utc),
        stage=2,
        status_short=3,
        status_long="Game Finished",
        periods_current=4,
        periods_total=4,
        periods_end_of_period=True,
        home_team_id=1,
        away_team_id=2,
    )
    db.add(g)
    db.commit()
    return g


@pytest.fixture
def jogador(db):
    from app.db.models import Player
    p = Player(id=501, firstname="LeBron", lastname="James", birth_country="USA", nba_start=2003)
    db.add(p)
    db.commit()
    return p


@pytest.fixture
def usuario(db):
    from app.db.models import User
    from app.auth.auth import hash_password
    u = User(
        email="teste@nba.com",
        full_name="Usuario Teste",
        birth_date=date(1990, 6, 15),
        hashed_password=hash_password("senha123"),
        is_active=True,
        email_confirmed=True,
        role="user",
        created_at=datetime.now(timezone.utc),
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def usuario_admin(db):
    from app.db.models import User
    from app.auth.auth import hash_password
    u = User(
        email="admin@nba.com",
        full_name="Admin NBA",
        birth_date=date(1985, 3, 10),
        hashed_password=hash_password("admin123"),
        is_active=True,
        email_confirmed=True,
        role="admin",
        created_at=datetime.now(timezone.utc),
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def token_usuario(usuario):
    from app.auth.auth import create_access_token
    return create_access_token({"sub": usuario.email})


@pytest.fixture
def token_admin(usuario_admin):
    from app.auth.auth import create_access_token
    return create_access_token({"sub": usuario_admin.email})


@pytest.fixture
def headers_usuario(token_usuario):
    return {"Authorization": f"Bearer {token_usuario}"}


@pytest.fixture
def headers_admin(token_admin):
    return {"Authorization": f"Bearer {token_admin}"}