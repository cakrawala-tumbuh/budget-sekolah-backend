"""
CRUD gabungan untuk DepreciationOldAsset, ContributionRate, dan ContributionAllocation.

- `get_rates` mengembalikan tarif efektif dengan fallback ke DEFAULT_RATES.
- `upsert_rates` memperbarui atau membuat baris ContributionRate sekaligus.
- `list_allocations` mengembalikan semua alokasi yang diterima oleh org tertentu.
"""
from sqlalchemy.orm import Session

from ..models.depreciation import DepreciationOldAsset
from ..models.contribution_rate import ContributionRate, DEFAULT_RATES
from ..models.contribution_allocation import ContributionAllocation
from ..schemas.depreciation import DepreciationOldAssetCreate, DepreciationOldAssetUpdate
from ..schemas.contribution import (
    ContributionRateSet,
    ContributionAllocationCreate,
    ContributionAllocationUpdate,
)


# ── Depreciation Old Assets ───────────────────────────────────────────────────

def list_dep_by_org(db: Session, org_id: int) -> list[DepreciationOldAsset]:
    return db.query(DepreciationOldAsset).filter(
        DepreciationOldAsset.organization_id == org_id
    ).all()


def get_dep(db: Session, dep_id: int) -> DepreciationOldAsset | None:
    return db.get(DepreciationOldAsset, dep_id)


def create_dep(db: Session, org_id: int, data: DepreciationOldAssetCreate) -> DepreciationOldAsset:
    obj = DepreciationOldAsset(organization_id=org_id, **data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_dep(
    db: Session, dep: DepreciationOldAsset, data: DepreciationOldAssetUpdate
) -> DepreciationOldAsset:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(dep, key, value)
    db.commit()
    db.refresh(dep)
    return dep


def delete_dep(db: Session, dep: DepreciationOldAsset) -> None:
    db.delete(dep)
    db.commit()


# ── Contribution Rates ────────────────────────────────────────────────────────

def get_rates(db: Session, org_id: int) -> dict[str, float]:
    rows = db.query(ContributionRate).filter(ContributionRate.organization_id == org_id).all()
    result = {**DEFAULT_RATES}
    for r in rows:
        result[r.rate_key] = r.rate_value
    return result


def upsert_rates(db: Session, org_id: int, data: ContributionRateSet) -> dict[str, float]:
    existing = {
        r.rate_key: r
        for r in db.query(ContributionRate).filter(
            ContributionRate.organization_id == org_id
        ).all()
    }
    for key, value in data.model_dump().items():
        if key in existing:
            existing[key].rate_value = value
        else:
            db.add(ContributionRate(organization_id=org_id, rate_key=key, rate_value=value))
    db.commit()
    return get_rates(db, org_id)


# ── Contribution Allocations ──────────────────────────────────────────────────

def list_allocations(db: Session, to_org_id: int) -> list[ContributionAllocation]:
    return db.query(ContributionAllocation).filter(
        ContributionAllocation.to_organization_id == to_org_id
    ).all()


def get_allocation(db: Session, alloc_id: int) -> ContributionAllocation | None:
    return db.get(ContributionAllocation, alloc_id)


def upsert_allocation(
    db: Session, to_org_id: int, data: ContributionAllocationCreate
) -> ContributionAllocation:
    obj = (
        db.query(ContributionAllocation)
        .filter(
            ContributionAllocation.from_organization_id == data.from_organization_id,
            ContributionAllocation.to_organization_id == to_org_id,
        )
        .first()
    )
    if obj is None:
        obj = ContributionAllocation(
            to_organization_id=to_org_id, **data.model_dump()
        )
        db.add(obj)
    else:
        for key, value in data.model_dump().items():
            setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def update_allocation(
    db: Session, alloc: ContributionAllocation, data: ContributionAllocationUpdate
) -> ContributionAllocation:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(alloc, key, value)
    db.commit()
    db.refresh(alloc)
    return alloc


def delete_allocation(db: Session, alloc: ContributionAllocation) -> None:
    db.delete(alloc)
    db.commit()
