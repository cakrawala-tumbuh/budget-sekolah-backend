"""Pytest fixtures used across the entire test suite."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.auth import get_current_user
from app.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole

# Ensure all models are imported before create_all is called
import app.models as _models  # noqa: F401
from app.crud.income_category import (
    seed_ypii_defaults as _seed_income,
    get_code_to_id_map as _income_code_to_id_map,
)
from app.crud.investment_category import seed_ypii_defaults as _seed_invest
from app.crud.expense_category import seed_ypii_defaults as _seed_expense

# SQLite in-memory with a shared connection — all sessions use the same connection
# so that tables created in engine_fixture remain visible in db_session.
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine_fixture():
    eng = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        # Force a single shared connection across the entire pytest session
        poolclass=None,
    )
    # Enable foreign key enforcement for SQLite
    @event.listens_for(eng, "connect")
    def set_sqlite_pragma(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(bind=eng)

    # Seed default YPII categories into the test DB
    SeedSession = sessionmaker(bind=eng)
    seed_db = SeedSession()
    try:
        _seed_income(seed_db)
        _seed_invest(seed_db)
        income_map = _income_code_to_id_map(seed_db)
        _seed_expense(seed_db, income_map)
    finally:
        seed_db.close()

    yield eng
    Base.metadata.drop_all(bind=eng)


@pytest.fixture()
def db_session(engine_fixture):
    connection = engine_fixture.connect()
    trans = connection.begin()
    Session = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        connection.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Override auth dependency agar semua test berjalan sebagai admin
    # tanpa perlu token JWT yang valid
    fake_admin = User(
        id=9999,
        username="admin",
        hashed_password="",
        role=UserRole.ADMIN,
        org_id=None,
        is_active=True,
    )

    def override_get_current_user():
        return fake_admin

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

