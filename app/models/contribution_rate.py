"""
Model tarif kontribusi per organisasi (ContributionRate).

Menyimpan override persentase kontribusi dari UNIT ke CABANG/PUSAT.
Jika tidak ada baris untuk organisasi tertentu, DEFAULT_RATES digunakan.
Kunci tarif (rate_key) didefinisikan di RATE_KEYS.
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


# Supported contribution rate keys
RATE_KEYS = [
    "up_to_pusat",            # % of UP sent to PUSAT          default 4%
    "up_to_cabang",           # % of UP sent to CABANG         default 12%
    "us_to_pusat",            # % of US sent to PUSAT          default 5%
    "us_to_cabang",           # % of US sent to CABANG         default 10%
    "development_fund",       # % of UP for Development Fund   default 20%
    "deficit_reserve",        # % of UP for Deficit Reserve    default 5%
    "social_care",            # % of revenue for Social Care   default 3%
    "teacher_study",          # % of revenue for Teacher Study default 3%
]

DEFAULT_RATES: dict[str, float] = {
    "up_to_pusat": 0.04,
    "up_to_cabang": 0.12,
    "us_to_pusat": 0.05,
    "us_to_cabang": 0.10,
    "development_fund": 0.20,
    "deficit_reserve": 0.05,
    "social_care": 0.03,
    "teacher_study": 0.03,
}


class ContributionRate(Base):
    """Per-organization contribution rates. Falls back to DEFAULT_RATES if no custom entry exists."""

    __tablename__ = "contribution_rates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, index=True
    )
    rate_key: Mapped[str] = mapped_column(String(50), nullable=False)
    rate_value: Mapped[float] = mapped_column(Float, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    organization: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization", back_populates="contribution_rates"
    )
