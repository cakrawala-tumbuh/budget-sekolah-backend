"""
Konfigurasi SQLAlchemy — engine, session factory, base model, dan dependency `get_db`.

Pola penggunaan di router/service:
    db: Session = Depends(get_db)

Untuk testing, gunakan engine in-memory dengan connection-level binding
sebagaimana dikonfigurasi di tests/conftest.py.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from .config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """
    FastAPI dependency yang menyediakan sesi database per request.

    Gunakan sebagai: ``db: Session = Depends(get_db)``
    Sesi otomatis ditutup setelah request selesai, berhasil maupun gagal.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
