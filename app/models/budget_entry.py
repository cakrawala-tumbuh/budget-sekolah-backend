"""
Model entri anggaran biaya per kategori per organisasi (BudgetEntry).

Setiap baris merepresentasikan satu rincian biaya pada satu ExpenseCategory.
Kolom `foundation` = dana Yayasan (kolom D di Excel),
`bos` = dana BOS/BOP/PBOS (kolom E). Total = foundation + bos.

ExpenseCategory menentukan apakah biaya ini:
  - is_operational: operasional (5110–5250) atau non-operasional (5500–5590)
  - is_up_component: masuk komponen UP
  - is_direct_income: langsung menjadi pendapatan tertentu
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class BudgetEntry(Base):
    """Budget line item per expense category per organization."""

    __tablename__ = "budget_entries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, index=True
    )
    expense_category_id: Mapped[int] = mapped_column(
        ForeignKey("expense_categories.id"), nullable=False, index=True
    )

    # Urutan rincian dalam satu kategori (1, 2, 3, …)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    description: Mapped[str | None] = mapped_column(String(500))
    basis: Mapped[str | None] = mapped_column(String(500))

    # Kolom D — dana Yayasan (UNIT) / anggaran (CABANG/PUSAT)
    foundation: Mapped[float] = mapped_column(Float, default=0.0)
    # Kolom E — dana BOS/BOP/PBOS (UNIT only); 0 untuk CABANG/PUSAT
    bos: Mapped[float] = mapped_column(Float, default=0.0)

    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization", back_populates="budget_entries"
    )
    expense_category: Mapped["ExpenseCategory"] = relationship(  # noqa: F821
        "ExpenseCategory", back_populates="budget_entries"
    )
    grade_allocations: Mapped[list["BudgetEntryGradeAllocation"]] = relationship(  # noqa: F821
        "BudgetEntryGradeAllocation",
        back_populates="budget_entry",
        cascade="all, delete-orphan",
    )

    @property
    def total(self) -> float:
        return (self.foundation or 0.0) + (self.bos or 0.0)
