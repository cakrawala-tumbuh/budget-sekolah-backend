"""
Model subsidi dari Cabang/Pusat ke unit anak (Subsidy).

Setiap baris menyatakan bahwa organisasi pemberi (CABANG atau PUSAT)
memberikan subsidi sejumlah `amount` kepada organisasi penerima:
  - Di sisi pemberi: muncul sebagai BEBAN pada `expense_category` (mis. 5590.07
    "Subsidi ke Unit"), kategori non-operasional sehingga tidak ikut komponen UP/US.
  - Di sisi penerima: muncul sebagai PENDAPATAN pada `income_category`.

Aturan keterhubungan:
  - CABANG dapat memberi subsidi ke UNIT anaknya.
  - PUSAT dapat memberi subsidi ke CABANG atau UNIT mana pun.

Berbeda dengan ParentExpenseAllocation yang mendistribusikan biaya induk secara
proporsional ke komponen UP/US unit, subsidi adalah transfer langsung: beban di
induk menjadi pendapatan di penerima tanpa menambah dasar biaya (cost base) unit.
"""
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Subsidy(Base):
    """Subsidi langsung dari Cabang/Pusat ke unit penerima."""

    __tablename__ = "subsidies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Organisasi pemberi subsidi (CABANG atau PUSAT)
    provider_org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, index=True
    )
    # Organisasi penerima subsidi (CABANG atau UNIT)
    recipient_org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, index=True
    )

    # Kategori beban di pemberi
    expense_category_id: Mapped[int] = mapped_column(
        ForeignKey("expense_categories.id"), nullable=False, index=True
    )
    # Kategori pendapatan di penerima
    income_category_id: Mapped[int] = mapped_column(
        ForeignKey("income_categories.id"), nullable=False, index=True
    )

    # Nominal subsidi (Rupiah)
    amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Dapat dinonaktifkan sementara tanpa menghapus konfigurasi
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    # Relationships
    provider_org: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization", foreign_keys=[provider_org_id]
    )
    recipient_org: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization", foreign_keys=[recipient_org_id]
    )
    expense_category: Mapped["ExpenseCategory"] = relationship(  # noqa: F821
        "ExpenseCategory", foreign_keys=[expense_category_id]
    )
    income_category: Mapped["IncomeCategory"] = relationship(  # noqa: F821
        "IncomeCategory", foreign_keys=[income_category_id]
    )
