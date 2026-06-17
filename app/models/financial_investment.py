"""
Model investasi keuangan CABANG/PUSAT (saham, reksa dana, obligasi, deposito, dll.).

Berbeda dari Investment (aset tetap), model ini mencatat instrumen keuangan yang
dibeli oleh CABANG atau PUSAT. Total investasi dialokasikan ke unit anak secara
proporsional berdasarkan new_students (pct_up), dan muncul sebagai beban UP di
simulasi unit penerima.
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

import enum


class InstrumentType(str, enum.Enum):
    SAHAM = "SAHAM"
    REKSA_DANA = "REKSA_DANA"
    OBLIGASI = "OBLIGASI"
    DEPOSITO = "DEPOSITO"
    LAINNYA = "LAINNYA"


def _now() -> datetime:
    return datetime.now(timezone.utc)


class FinancialInvestment(Base):
    """Instrumen investasi keuangan milik CABANG atau PUSAT."""

    __tablename__ = "financial_investments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, index=True
    )
    instrument_type: Mapped[InstrumentType] = mapped_column(
        Enum(InstrumentType), nullable=False
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    organization: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization", back_populates="financial_investments"
    )
