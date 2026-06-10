"""
CRUD untuk BudgetEntry (entri anggaran biaya per kategori).

Fungsi `list_by_org` mengembalikan semua baris diurutkan per expense_category_id + line_number.
Fungsi `bulk_create` untuk import sekaligus banyak baris dalam satu transaksi.
Fungsi `delete_by_org_and_category` menghapus semua rincian suatu kategori sekaligus.
"""
from sqlalchemy.orm import Session

from ..models.budget_entry import BudgetEntry
from ..schemas.budget_entry import BudgetEntryCreate, BudgetEntryUpdate


def list_by_org(db: Session, org_id: int) -> list[BudgetEntry]:
    return (
        db.query(BudgetEntry)
        .filter(BudgetEntry.organization_id == org_id)
        .order_by(BudgetEntry.expense_category_id, BudgetEntry.line_number)
        .all()
    )


def list_by_category(db: Session, org_id: int, expense_category_id: int) -> list[BudgetEntry]:
    return (
        db.query(BudgetEntry)
        .filter(
            BudgetEntry.organization_id == org_id,
            BudgetEntry.expense_category_id == expense_category_id,
        )
        .order_by(BudgetEntry.line_number)
        .all()
    )


def get(db: Session, entry_id: int) -> BudgetEntry | None:
    return db.get(BudgetEntry, entry_id)


def create(db: Session, org_id: int, data: BudgetEntryCreate) -> BudgetEntry:
    obj = BudgetEntry(organization_id=org_id, **data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def bulk_create(db: Session, org_id: int, entries: list[BudgetEntryCreate]) -> list[BudgetEntry]:
    objs = [BudgetEntry(organization_id=org_id, **e.model_dump()) for e in entries]
    db.add_all(objs)
    db.commit()
    for o in objs:
        db.refresh(o)
    return objs


def update(db: Session, entry: BudgetEntry, data: BudgetEntryUpdate) -> BudgetEntry:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(entry, key, value)
    db.commit()
    db.refresh(entry)
    return entry


def delete(db: Session, entry: BudgetEntry) -> None:
    db.delete(entry)
    db.commit()


def bulk_move_category(
    db: Session,
    org_id: int,
    entry_ids: list[int],
    expense_category_id: int,
) -> list[BudgetEntry]:
    """Pindahkan sejumlah entri ke kategori biaya baru dalam satu transaksi.

    Args:
        db: Database session.
        org_id: ID organisasi — hanya entri milik org ini yang diubah.
        entry_ids: Daftar ID entri yang akan dipindahkan.
        expense_category_id: ID kategori tujuan.

    Returns:
        Daftar entri yang berhasil diperbarui.
    """
    entries = (
        db.query(BudgetEntry)
        .filter(
            BudgetEntry.id.in_(entry_ids),
            BudgetEntry.organization_id == org_id,
        )
        .all()
    )
    for entry in entries:
        entry.expense_category_id = expense_category_id
    db.commit()
    for entry in entries:
        db.refresh(entry)
    return entries


def delete_by_org_and_category(db: Session, org_id: int, expense_category_id: int) -> int:
    """Hapus semua rincian suatu kategori biaya. Returns jumlah baris dihapus."""
    n = (
        db.query(BudgetEntry)
        .filter(
            BudgetEntry.organization_id == org_id,
            BudgetEntry.expense_category_id == expense_category_id,
        )
        .delete()
    )
    db.commit()
    return n
