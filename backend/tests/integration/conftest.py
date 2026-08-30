"""Integration tests run against the real `policylens_test` Postgres database (see
docker-compose.yml's init script) pre-loaded with the real supplied corpus - this
exercises actual FTS/SQL behavior rather than mocking the database away."""

import pytest
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import make_engine


@pytest.fixture(scope="session")
def engine():
    eng = make_engine(get_settings().database_url_test)
    try:
        with eng.connect():
            pass
    except Exception as exc:  # pragma: no cover - environment-dependent
        pytest.skip(f"policylens_test database not reachable: {exc}")
    return eng


@pytest.fixture
def db_session(engine):
    with Session(engine) as session:
        yield session
