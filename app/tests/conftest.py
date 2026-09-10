import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import URL, make_url
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

DEFAULT_DATABASE_URL = "postgresql://admin:S3cur3P4ss!@db:5432/users_db"


def _test_database_url() -> URL:
    """
    URL de la base de datos de pruebas.

    Se deriva de DATABASE_URL añadiendo el sufijo `_test` al nombre, de modo
    que los tests nunca escriben sobre la base de datos de desarrollo aunque
    se ejecuten dentro del mismo contenedor.
    """
    explicit = os.getenv("TEST_DATABASE_URL")
    if explicit:
        return make_url(explicit)

    base = make_url(os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))
    return base.set(database=f"{base.database}_test")


def _ensure_database_exists(url: URL) -> None:
    """Crea la base de datos de pruebas si todavía no existe."""
    admin_engine = create_engine(
        url.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
    )
    try:
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": url.database},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    finally:
        admin_engine.dispose()


@pytest.fixture(scope="session")
def engine():
    url = _test_database_url()
    _ensure_database_exists(url)

    test_engine = create_engine(url, pool_pre_ping=True)
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    test_engine.dispose()


@pytest.fixture(autouse=True)
def clean_tables(engine):
    """Deja la tabla vacía y el contador de IDs a cero antes de cada test."""
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture
def db_session(session_factory):
    """Sesión directa, para comprobar en la BD lo que la API no expone."""
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(session_factory):
    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    # Sin context manager a propósito: así no se dispara el lifespan, que
    # abriría conexiones contra la base de datos real de la aplicación.
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def user_payload():
    return {
        "name": "Ana García",
        "email": "ana.garcia@example.com",
        "password": "Segura123!",
    }


@pytest.fixture
def created_user(client, user_payload):
    response = client.post("/users/", json=user_payload)
    assert response.status_code == 201
    return response.json()
