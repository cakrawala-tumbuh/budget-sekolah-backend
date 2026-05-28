"""
Model alokasi beban kegiatan per grade (BudgetEntryGradeAllocation).

Digunakan ketika BudgetEntry terhubung ke ExpenseCategory yang
is_direct_income=True dan IncomeCategory-nya ber-calc_method=GRADE_BASED.

User dapat memilah total biaya kegiatan ke grade tertentu sehingga
tarif per grade dapat dihitung: amount_grade_N / students_grade_N.
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class BudgetEntryGradeAllocation(Base):
    """Alokasi jumlah biaya kegiatan ke satu grade level."""

    __tablename__ = "budget_entry_grade_allocations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    budget_entry_id: Mapped[int] = mapped_column(
        ForeignKey("budget_entries.id"), nullable=False, index=True
    )

    # Slot grade: "grade_1" … "grade_6" — sesuai konvensi GradeConfig
    grade_slot: Mapped[str] = mapped_column(String(20), nullable=False)

    amount: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    # Relationships
    budget_entry: Mapped["BudgetEntry"] = relationship(  # noqa: F821
        "BudgetEntry", back_populates="grade_allocations"
    )
