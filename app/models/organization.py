from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import String, DateTime, ForeignKey, Enum, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class OrgType(str, PyEnum):
    UNIT = "UNIT"
    CABANG = "CABANG"
    PUSAT = "PUSAT"


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    org_type: Mapped[OrgType] = mapped_column(Enum(OrgType), nullable=False)
    city: Mapped[str | None] = mapped_column(String(100))
    # Saldo kas & setara kas awal (opening balance). Dipakai sebagai dasar
    # perhitungan budget kas (saldo kas akhir = saldo awal + surplus/defisit kas).
    cash_balance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    # UNIT → parent is CABANG; CABANG → parent is PUSAT
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    # Relationships
    parent: Mapped["Organization | None"] = relationship(
        "Organization", remote_side="Organization.id", back_populates="children"
    )
    children: Mapped[list["Organization"]] = relationship(
        "Organization", back_populates="parent"
    )
    assumption: Mapped["UnitAssumption | None"] = relationship(  # noqa: F821
        "UnitAssumption", back_populates="organization", uselist=False
    )
    grade_config: Mapped["GradeConfig | None"] = relationship(  # noqa: F821
        "GradeConfig", back_populates="organization", uselist=False
    )
    budget_entries: Mapped[list["BudgetEntry"]] = relationship(  # noqa: F821
        "BudgetEntry", back_populates="organization"
    )
    investments: Mapped[list["Investment"]] = relationship(  # noqa: F821
        "Investment", back_populates="organization"
    )
    depreciation_old_assets: Mapped[list["DepreciationOldAsset"]] = relationship(  # noqa: F821
        "DepreciationOldAsset", back_populates="organization"
    )
    contribution_rates: Mapped[list["ContributionRate"]] = relationship(  # noqa: F821
        "ContributionRate", back_populates="organization"
    )
    # Contribution allocations received by this org (as to_organization)
    received_allocations: Mapped[list["ContributionAllocation"]] = relationship(  # noqa: F821
        "ContributionAllocation",
        foreign_keys="ContributionAllocation.to_organization_id",
        back_populates="to_organization",
    )
    # Contribution allocations sent by this org (as from_organization)
    sent_allocations: Mapped[list["ContributionAllocation"]] = relationship(  # noqa: F821
        "ContributionAllocation",
        foreign_keys="ContributionAllocation.from_organization_id",
        back_populates="from_organization",
    )
    income_entries: Mapped[list["IncomeEntry"]] = relationship(  # noqa: F821
        "IncomeEntry", back_populates="organization"
    )
    parent_expense_allocations: Mapped[list["ParentExpenseAllocation"]] = relationship(  # noqa: F821
        "ParentExpenseAllocation",
        foreign_keys="ParentExpenseAllocation.parent_org_id",
        back_populates="parent_org",
    )
    direct_income_overrides: Mapped[list["DirectIncomeOverride"]] = relationship(  # noqa: F821
        "DirectIncomeOverride", back_populates="organization"
    )
