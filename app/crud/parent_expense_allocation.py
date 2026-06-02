"""
CRUD untuk ParentExpenseAllocation — konfigurasi alokasi biaya dari Cabang/Pusat
ke unit-unit anak.
"""
from sqlalchemy.orm import Session

from ..models.parent_expense_allocation import ParentExpenseAllocation
from ..schemas.parent_expense_allocation import (
    ParentExpenseAllocationCreate,
    ParentExpenseAllocationUpdate,
)


def list_by_org(db: Session, parent_org_id: int) -> list[ParentExpenseAllocation]:
    """Kembalikan semua konfigurasi alokasi untuk organisasi induk tertentu."""
    return (
        db.query(ParentExpenseAllocation)
        .filter(ParentExpenseAllocation.parent_org_id == parent_org_id)
        .order_by(ParentExpenseAllocation.id)
        .all()
    )


def list_active_by_org(db: Session, parent_org_id: int) -> list[ParentExpenseAllocation]:
    """Kembalikan hanya konfigurasi alokasi yang aktif untuk organisasi induk tertentu."""
    return (
        db.query(ParentExpenseAllocation)
        .filter(
            ParentExpenseAllocation.parent_org_id == parent_org_id,
            ParentExpenseAllocation.is_active == True,  # noqa: E712
        )
        .order_by(ParentExpenseAllocation.id)
        .all()
    )


def get(db: Session, alloc_id: int) -> ParentExpenseAllocation | None:
    return db.get(ParentExpenseAllocation, alloc_id)


def create(
    db: Session, parent_org_id: int, data: ParentExpenseAllocationCreate
) -> ParentExpenseAllocation:
    """Buat konfigurasi alokasi baru. Raises IntegrityError jika (org, category) sudah ada."""
    obj = ParentExpenseAllocation(parent_org_id=parent_org_id, **data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(
    db: Session,
    alloc: ParentExpenseAllocation,
    data: ParentExpenseAllocationUpdate,
) -> ParentExpenseAllocation:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(alloc, key, value)
    db.commit()
    db.refresh(alloc)
    return alloc


def delete(db: Session, alloc: ParentExpenseAllocation) -> None:
    db.delete(alloc)
    db.commit()


def copy_from(
    db: Session,
    target_org_id: int,
    source_org_id: int,
    affects_up: bool | None = None,
) -> dict:
    """Salin alokasi dari source_org ke target_org, lewati yang sudah ada."""
    query = db.query(ParentExpenseAllocation).filter(
        ParentExpenseAllocation.parent_org_id == source_org_id
    )
    if affects_up is not None:
        query = query.filter(ParentExpenseAllocation.affects_up == affects_up)
    source_allocs = query.all()

    existing_cat_ids = {
        a.expense_category_id
        for a in db.query(ParentExpenseAllocation)
        .filter(ParentExpenseAllocation.parent_org_id == target_org_id)
        .all()
    }

    copied = 0
    skipped = 0
    for alloc in source_allocs:
        if alloc.expense_category_id in existing_cat_ids:
            skipped += 1
            continue
        db.add(ParentExpenseAllocation(
            parent_org_id=target_org_id,
            expense_category_id=alloc.expense_category_id,
            affects_up=alloc.affects_up,
            is_active=alloc.is_active,
        ))
        copied += 1

    if copied > 0:
        db.commit()

    return {"copied": copied, "skipped": skipped}
