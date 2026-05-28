"""
CRUD untuk IncomeEntry (pendapatan manual per organisasi).
"""
from sqlalchemy.orm import Session

from ..models.income_entry import IncomeEntry
from ..schemas.income_entry import IncomeEntryCreate, IncomeEntryUpdate


def list_by_org(db: Session, org_id: int) -> list[IncomeEntry]:
    return (
        db.query(IncomeEntry)
        .filter(IncomeEntry.organization_id == org_id)
        .order_by(IncomeEntry.income_category_id, IncomeEntry.line_number)
        .all()
    )


def list_by_category(db: Session, org_id: int, income_category_id: int) -> list[IncomeEntry]:
    return (
        db.query(IncomeEntry)
        .filter(
            IncomeEntry.organization_id == org_id,
            IncomeEntry.income_category_id == income_category_id,
        )
        .order_by(IncomeEntry.line_number)
        .all()
    )


def get(db: Session, entry_id: int) -> IncomeEntry | None:
    return db.get(IncomeEntry, entry_id)


def create(db: Session, org_id: int, data: IncomeEntryCreate) -> IncomeEntry:
    obj = IncomeEntry(organization_id=org_id, **data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def bulk_create(db: Session, org_id: int, entries: list[IncomeEntryCreate]) -> list[IncomeEntry]:
    objs = [IncomeEntry(organization_id=org_id, **e.model_dump()) for e in entries]
    db.add_all(objs)
    db.commit()
    for o in objs:
        db.refresh(o)
    return objs


def update(db: Session, entry: IncomeEntry, data: IncomeEntryUpdate) -> IncomeEntry:
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(entry, k, v)
    db.commit()
    db.refresh(entry)
    return entry


def delete(db: Session, entry: IncomeEntry) -> None:
    db.delete(entry)
    db.commit()


def delete_by_org_and_category(db: Session, org_id: int, income_category_id: int) -> int:
    """Hapus semua rincian suatu kategori pendapatan. Returns jumlah baris dihapus."""
    n = (
        db.query(IncomeEntry)
        .filter(
            IncomeEntry.organization_id == org_id,
            IncomeEntry.income_category_id == income_category_id,
        )
        .delete()
    )
    db.commit()
    return n
