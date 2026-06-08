"""
Model kategori biaya (ExpenseCategory).

Menggantikan AccountCodeRule dan constants/account_codes.py dengan satu
sumber kebenaran yang dapat dikonfigurasi melalui API.

Setiap baris merepresentasikan satu kategori biaya (level akun detail, mis. "5130.01")
yang dapat ditandai sebagai:
  - is_up_component: masuk komponen UP (Uang Pangkal)
  - is_direct_income: biaya ini langsung menghasilkan pendapatan tertentu
  - contribution_role: untuk akun kontribusi keluar (5590.xx)
"""
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ExpenseCategory(Base):
    """Kategori biaya operasional dan non-operasional."""

    __tablename__ = "expense_categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Kode akun, e.g. "5130.01" atau "5110" (untuk kelompok)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    label: Mapped[str] = mapped_column(String(200), nullable=False)

    # True = biaya operasional (5110–5250), False = non-operasional (5500–5590)
    is_operational: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # True = masuk komponen UP (biasanya 5130.xx)
    is_up_component: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # True = biaya ini langsung menjadi pendapatan (Direct Income)
    is_direct_income: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Untuk is_direct_income=True: FK ke IncomeCategory tujuan
    maps_to_income_category_id: Mapped[int | None] = mapped_column(
        ForeignKey("income_categories.id"), nullable=True
    )

    # Untuk akun kontribusi keluar (5590.xx): peran kontribusi
    # e.g. "up_to_pusat", "us_to_cabang", "development_fund"
    contribution_role: Mapped[str | None] = mapped_column(String(50))

    # Urutan tampil
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    # Relationships
    maps_to_income_category: Mapped["IncomeCategory | None"] = relationship(  # noqa: F821
        "IncomeCategory",
        foreign_keys=[maps_to_income_category_id],
        back_populates="source_expense_categories",
    )
    budget_entries: Mapped[list["BudgetEntry"]] = relationship(  # noqa: F821
        "BudgetEntry", back_populates="expense_category"
    )
    direct_income_overrides: Mapped[list["DirectIncomeOverride"]] = relationship(  # noqa: F821
        "DirectIncomeOverride", back_populates="expense_category"
    )
