"""
Model alokasi kontribusi antar organisasi (ContributionAllocation).

Mencatat alokasi kontribusi dari unit ke cabang atau dari cabang ke pusat.
Setiap pasang (from_organization_id, to_organization_id) unik.
Digunakan oleh simulate_allocation() untuk menghitung distribusi UP/US
berbasis jumlah siswa proporsional.
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Float, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ContributionAllocation(Base):
    """
    Contribution allocation from unit/branch to branch/central.
    Stores student counts and optional US/UP contribution percentage overrides.
    """

    __tablename__ = "contribution_allocations"
    __table_args__ = (
        UniqueConstraint("from_organization_id", "to_organization_id", name="uq_alloc_from_to"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    from_organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, index=True
    )
    to_organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, index=True
    )
    total_students: Mapped[int] = mapped_column(Integer, default=0)
    new_students: Mapped[int] = mapped_column(Integer, default=0)

    # None = compute proportionally from total_students / sum of all units
    override_pct_us: Mapped[float | None] = mapped_column(Float)
    override_pct_up: Mapped[float | None] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    from_organization: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization",
        foreign_keys=[from_organization_id],
        back_populates="sent_allocations",
    )
    to_organization: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization",
        foreign_keys=[to_organization_id],
        back_populates="received_allocations",
    )
