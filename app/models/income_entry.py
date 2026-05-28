"""
Model entri pendapatan manual (IncomeEntry).

Hanya untuk IncomeCategory dengan calc_method=MANUAL.
Struktur mirip BudgetEntry: satu kategori bisa punya banyak baris rincian.
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class IncomeEntry(Base):
    """Rincian entri pendapatan manual per kategori per organisasi."""

    __tablename__ = "income_entries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, index=True
    )
    income_category_id: Mapped[int] = mapped_column(
        ForeignKey("income_categories.id"), nullable=False, index=True
    )

    # Urutan rincian dalam satu kategori (1, 2, 3, …)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    description: Mapped[str | None] = mapped_column(String(500))
    basis: Mapped[str | None] = mapped_column(String(500))
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization", back_populates="income_entries"
    )
    income_category: Mapped["IncomeCategory"] = relationship(  # noqa: F821
        "IncomeCategory", back_populates="income_entries"
    )
