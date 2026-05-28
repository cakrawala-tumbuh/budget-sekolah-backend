"""
CRUD untuk GradeAllocation (alokasi biaya kegiatan per grade).
"""
from sqlalchemy.orm import Session

from ..models.budget_entry_grade_allocation import BudgetEntryGradeAllocation
from ..schemas.grade_allocation import GradeAllocationCreate, GradeAllocationUpdate


def list_by_entry(db: Session, budget_entry_id: int) -> list[BudgetEntryGradeAllocation]:
    return (
        db.query(BudgetEntryGradeAllocation)
        .filter(BudgetEntryGradeAllocation.budget_entry_id == budget_entry_id)
        .order_by(BudgetEntryGradeAllocation.grade_slot)
        .all()
    )


def get(db: Session, alloc_id: int) -> BudgetEntryGradeAllocation | None:
    return db.get(BudgetEntryGradeAllocation, alloc_id)


def get_by_slot(db: Session, budget_entry_id: int, grade_slot: str) -> BudgetEntryGradeAllocation | None:
    return (
        db.query(BudgetEntryGradeAllocation)
        .filter(
            BudgetEntryGradeAllocation.budget_entry_id == budget_entry_id,
            BudgetEntryGradeAllocation.grade_slot == grade_slot,
        )
        .first()
    )


def upsert(db: Session, budget_entry_id: int, data: GradeAllocationCreate) -> BudgetEntryGradeAllocation:
    """Buat atau update alokasi untuk grade_slot tertentu."""
    existing = get_by_slot(db, budget_entry_id, data.grade_slot)
    if existing:
        existing.amount = data.amount
        db.commit()
        db.refresh(existing)
        return existing
    obj = BudgetEntryGradeAllocation(budget_entry_id=budget_entry_id, **data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, alloc: BudgetEntryGradeAllocation, data: GradeAllocationUpdate) -> BudgetEntryGradeAllocation:
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(alloc, k, v)
    db.commit()
    db.refresh(alloc)
    return alloc


def delete(db: Session, alloc: BudgetEntryGradeAllocation) -> None:
    db.delete(alloc)
    db.commit()


def delete_by_entry(db: Session, budget_entry_id: int) -> int:
    """Hapus semua alokasi untuk satu BudgetEntry. Returns jumlah baris dihapus."""
    n = (
        db.query(BudgetEntryGradeAllocation)
        .filter(BudgetEntryGradeAllocation.budget_entry_id == budget_entry_id)
        .delete()
    )
    db.commit()
    return n
