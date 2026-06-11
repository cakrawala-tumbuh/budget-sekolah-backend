"""
Router entri pendapatan manual — CRUD untuk IncomeEntry.

Endpoint:
  GET    /organizations/{org_id}/income-entries                              — semua entri
  GET    /organizations/{org_id}/income-entries?category_id={id}            — filter per kategori
  POST   /organizations/{org_id}/income-entries                             — buat satu entri
  POST   /organizations/{org_id}/income-entries/bulk                        — buat banyak entri
  PUT    /organizations/{org_id}/income-entries/{entry_id}                  — update entri
  DELETE /organizations/{org_id}/income-entries/{entry_id}                  — hapus entri
  DELETE /organizations/{org_id}/income-entries/by-category/{category_id}   — hapus per kategori
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import get_org_access, require_not_locked
from ..database import get_db
from ..crud import income_entry as crud, organization as org_crud
from ..schemas.income_entry import (
    IncomeEntryCreate, IncomeEntryUpdate, IncomeEntryRead, IncomeEntryBulkCreate
)

router = APIRouter(
    prefix="/organizations/{org_id}/income-entries",
    tags=["Income Entries"],
    dependencies=[Depends(get_org_access)],
)


def _get_org_or_404(db: Session, org_id: int):
    org = org_crud.get(db, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.get("", response_model=list[IncomeEntryRead])
def list_entries(
    org_id: int,
    category_id: int | None = None,
    db: Session = Depends(get_db),
):
    _get_org_or_404(db, org_id)
    if category_id is not None:
        return crud.list_by_category(db, org_id, category_id)
    return crud.list_by_org(db, org_id)


@router.post("", response_model=IncomeEntryRead, status_code=status.HTTP_201_CREATED)
def create_entry(org_id: int, data: IncomeEntryCreate, db: Session = Depends(get_db), _=Depends(require_not_locked)):
    _get_org_or_404(db, org_id)
    return crud.create(db, org_id, data)


@router.post("/bulk", response_model=list[IncomeEntryRead], status_code=status.HTTP_201_CREATED)
def bulk_create_entries(org_id: int, data: IncomeEntryBulkCreate, db: Session = Depends(get_db), _=Depends(require_not_locked)):
    _get_org_or_404(db, org_id)
    return crud.bulk_create(db, org_id, data.entries)


@router.put("/{entry_id}", response_model=IncomeEntryRead)
def update_entry(org_id: int, entry_id: int, data: IncomeEntryUpdate, db: Session = Depends(get_db), _=Depends(require_not_locked)):
    _get_org_or_404(db, org_id)
    entry = crud.get(db, entry_id)
    if entry is None or entry.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Income entry not found")
    return crud.update(db, entry, data)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(org_id: int, entry_id: int, db: Session = Depends(get_db), _=Depends(require_not_locked)):
    _get_org_or_404(db, org_id)
    entry = crud.get(db, entry_id)
    if entry is None or entry.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Income entry not found")
    crud.delete(db, entry)


@router.delete("/by-category/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_by_category(org_id: int, category_id: int, db: Session = Depends(get_db), _=Depends(require_not_locked)):
    _get_org_or_404(db, org_id)
    crud.delete_by_org_and_category(db, org_id, category_id)
