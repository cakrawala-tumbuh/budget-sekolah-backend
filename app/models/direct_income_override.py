"""
Model override direct income per organisasi per expense category.

Ketika ada override, simulasi pendapatan menggunakan override_amount
sebagai pengganti nilai otomatis dari budget entry. Jika tidak ada
override, nilai otomatis tetap dipakai.
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Float, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class DirectIncomeOverride(Base):
    """Override nilai direct income per organisasi per expense category."""

    __tablename__ = "direct_income_overrides"
    __table_args__ = (
        UniqueConstraint("organization_id", "expense_category_id", name="uq_dio_org_expense"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, index=True
    )
    expense_category_id: Mapped[int] = mapped_column(
        ForeignKey("expense_categories.id"), nullable=False, index=True
    )
    override_amount: Mapped[float] = mapped_column(Float, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization", back_populates="direct_income_overrides"
    )
    expense_category: Mapped["ExpenseCategory"] = relationship(  # noqa: F821
        "ExpenseCategory", back_populates="direct_income_overrides"
    )
