"""
Model alokasi biaya dari organisasi induk (Cabang/Pusat) ke anak-anaknya
(ParentExpenseAllocation).

Setiap baris menandai bahwa suatu kategori biaya di organisasi induk
akan didistribusikan secara proporsional ke organisasi anak berdasarkan
jumlah siswa yang terdaftar di ContributionAllocation.

Alokasi menambah beban UP (affects_up=True) atau US (affects_up=False)
di organisasi anak terkait.

Distribusi proporsional menggunakan ContributionAllocation.new_students
untuk UP, dan ContributionAllocation.total_students untuk US.
Override proporsi per-anak menggunakan override_pct_up / override_pct_us
yang sudah ada di ContributionAllocation.
"""
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ParentExpenseAllocation(Base):
    """
    Konfigurasi alokasi biaya dari Cabang/Pusat ke unit-unit di bawahnya.

    Satu baris = satu kategori biaya di parent_org yang didistribusikan
    ke semua anak yang terdaftar di ContributionAllocation.
    """

    __tablename__ = "parent_expense_allocations"
    __table_args__ = (
        UniqueConstraint(
            "parent_org_id", "expense_category_id", name="uq_pea_org_cat"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Organisasi induk (CABANG atau PUSAT) yang memiliki beban biaya
    parent_org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, index=True
    )

    # Kategori biaya yang akan dialokasikan ke anak
    expense_category_id: Mapped[int] = mapped_column(
        ForeignKey("expense_categories.id"), nullable=False, index=True
    )

    # True  = menambah beban UP di anak (proporsi berdasar new_students)
    # False = menambah beban US di anak (proporsi berdasar total_students)
    affects_up: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Dapat dinonaktifkan sementara tanpa menghapus konfigurasi
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    # Relationships
    parent_org: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization",
        foreign_keys=[parent_org_id],
        back_populates="parent_expense_allocations",
    )
    expense_category: Mapped["ExpenseCategory"] = relationship(  # noqa: F821
        "ExpenseCategory",
        foreign_keys=[expense_category_id],
    )
