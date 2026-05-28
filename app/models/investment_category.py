"""
Model kategori investasi (InvestmentCategory).

Setiap baris merepresentasikan satu kategori aset tetap (1330.01–1330.08).
Semua investasi dan depresiasi aset baru otomatis masuk komponen UP.
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class InvestmentCategory(Base):
    """Kategori aset tetap baru untuk investasi."""

    __tablename__ = "investment_categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Kode akun YPII, e.g. "1330.01"
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    label: Mapped[str] = mapped_column(String(200), nullable=False)

    # Umur ekonomis default (tahun) untuk kategori ini
    default_economic_life: Mapped[int] = mapped_column(Integer, default=4)

    # Urutan tampil
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    # Relationships
    investments: Mapped[list["Investment"]] = relationship(  # noqa: F821
        "Investment", back_populates="investment_category"
    )
