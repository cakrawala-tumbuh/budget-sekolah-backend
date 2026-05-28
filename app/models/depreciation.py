"""
Model aset tetap lama yang masih dalam masa depresiasi (DepreciationOldAsset).

Sesuai dengan Tabel B di sheet "Depresiasi" pada template RAB Unit.
Depresiasi per tahun = acquisition_cost / useful_life (garis lurus).
Nilai buku = acquisition_cost − (dep_per_year × tahun_sudah_berlalu).
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class DepreciationOldAsset(Base):
    """Existing assets still being depreciated (Table B of the Depreciation sheet)."""

    __tablename__ = "depreciation_old_assets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, index=True
    )

    asset_code: Mapped[str | None] = mapped_column(String(50))
    asset_name: Mapped[str] = mapped_column(String(300), nullable=False)
    acquisition_cost: Mapped[float] = mapped_column(Float, nullable=False)
    useful_life: Mapped[int] = mapped_column(Integer, nullable=False)  # years
    acquisition_year: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    organization: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization", back_populates="depreciation_old_assets"
    )

    def dep_per_year(self) -> float:
        if self.useful_life <= 0:
            return 0.0
        return self.acquisition_cost / self.useful_life

    def dep_current_year(self, fiscal_year: int) -> float:
        """Depreciation for the current year. Zero if the asset's useful life has ended."""
        year_number = fiscal_year - self.acquisition_year + 1
        if year_number < 1 or year_number > self.useful_life:
            return 0.0
        return self.dep_per_year()

    def book_value(self, fiscal_year: int) -> float:
        years_elapsed = fiscal_year - self.acquisition_year
        already_depreciated = self.dep_per_year() * years_elapsed
        return max(0.0, self.acquisition_cost - already_depreciated)
