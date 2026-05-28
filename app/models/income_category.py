"""
Model kategori pendapatan (IncomeCategory).

Setiap baris merepresentasikan satu kategori pendapatan (4xxx).
Cara kalkulasi ditentukan oleh `calc_method`:

  MANUAL          → user input melalui IncomeEntry
  SIMULATED_UP    → dihitung otomatis dari simulasi UP
  SIMULATED_US    → dihitung otomatis dari simulasi US
  FROM_EXPENSE    → dijumlahkan dari BudgetEntry yang maps ke kategori ini
  GRADE_BASED     → dihitung dari BudgetEntryGradeAllocation (per grade)
  SUM_FROM_BOS    → dijumlahkan dari kolom `bos` seluruh BudgetEntry organisasi
"""
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class IncomeCalcMethod(str, PyEnum):
    MANUAL = "MANUAL"
    SIMULATED_UP = "SIMULATED_UP"
    SIMULATED_US = "SIMULATED_US"
    FROM_EXPENSE = "FROM_EXPENSE"
    GRADE_BASED = "GRADE_BASED"
    SUM_FROM_BOS = "SUM_FROM_BOS"


class IncomeCategory(Base):
    """Kategori pendapatan dan cara kalkulasinya."""

    __tablename__ = "income_categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Kode akun, e.g. "4110.01"
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    label: Mapped[str] = mapped_column(String(200), nullable=False)

    # Cara kalkulasi pendapatan ini
    calc_method: Mapped[IncomeCalcMethod] = mapped_column(
        Enum(IncomeCalcMethod), nullable=False, default=IncomeCalcMethod.MANUAL
    )

    # Urutan tampil
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    # Relationships
    # ExpenseCategory yang di-direct-income-kan ke kategori ini
    source_expense_categories: Mapped[list["ExpenseCategory"]] = relationship(  # noqa: F821
        "ExpenseCategory",
        foreign_keys="ExpenseCategory.maps_to_income_category_id",
        back_populates="maps_to_income_category",
    )
    income_entries: Mapped[list["IncomeEntry"]] = relationship(  # noqa: F821
        "IncomeEntry", back_populates="income_category"
    )
