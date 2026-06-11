"""
Model SQLAlchemy untuk entitas User (autentikasi).

Setiap user memiliki role ADMIN atau ORG.
- ADMIN: akses penuh ke semua resource.
- ORG: akses terbatas pada organisasi miliknya (org_id).

Admin dibuat otomatis saat startup. User ORG dibuat otomatis saat
organisasi baru dibuat, dengan password acak yang dikembalikan sekali.
"""
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class UserRole(str, PyEnum):
    ADMIN = "ADMIN"
    ORG = "ORG"


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    """
    Akun pengguna untuk autentikasi API.

    Atribut:
        id: Primary key.
        username: Nama pengguna unik; admin = 'admin', org = kode org lowercase.
        hashed_password: Password yang sudah di-hash dengan bcrypt.
        role: ADMIN atau ORG.
        org_id: FK ke organizations; hanya diisi untuk role ORG.
        is_active: False berarti akun dinonaktifkan.
        created_at: Waktu pembuatan.
        updated_at: Waktu update terakhir.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    org_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    token_version: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )
