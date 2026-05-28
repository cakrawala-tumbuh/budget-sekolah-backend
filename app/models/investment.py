"""
Model pembelian aset tetap baru dalam tahun anggaran berjalan (Investment).

Sesuai dengan sheet "4. Investasi" pada template RAB Unit.
Kategori aset ditentukan via FK ke InvestmentCategory (1330.01–1330.08).
Depresiasi proporsional dihitung otomatis berdasarkan nilai beli,
umur ekonomis (tahun), dan bulan mulai penggunaan.
Semua investasi dan depresiasi otomatis masuk komponen UP.
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Investment(Base):
    """New fixed asset purchases in the current fiscal year (sheet 4. Investments)."""

    __tablename__ = "investments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, index=True
    )
    # Kategori aset: FK ke InvestmentCategory (1330.01–1330.08)
    investment_category_id: Mapped[int] = mapped_column(
        ForeignKey("investment_categories.id"), nullable=False, index=True
    )

    asset_code: Mapped[str | None] = mapped_column(String(50))
    asset_name: Mapped[str] = mapped_column(String(300), nullable=False)
    purchase_price: Mapped[float] = mapped_column(Float, nullable=False)
    useful_life: Mapped[int] = mapped_column(Integer, nullable=False)   # years
    start_month: Mapped[int] = mapped_column(Integer, nullable=False)   # 1–12

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    organization: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization", back_populates="investments"
    )
    investment_category: Mapped["InvestmentCategory"] = relationship(  # noqa: F821
        "InvestmentCategory", back_populates="investments"
    )

    @property
    def dep_per_year(self) -> float:
        if self.useful_life <= 0:
            return 0.0
        return self.purchase_price / self.useful_life

    @property
    def dep_current_year(self) -> float:
        """Proportional depreciation: dep/yr * (13 - start_month) / 12."""
        month = max(1, min(12, self.start_month))
        return self.dep_per_year * (13 - month) / 12

    @property
    def end_book_value(self) -> float:
        return self.purchase_price - self.dep_current_year
