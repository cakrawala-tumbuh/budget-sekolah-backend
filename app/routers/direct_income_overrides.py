"""
Router override direct income per organisasi per expense category.

Endpoint:
  GET    /organizations/{org_id}/direct-income-overrides                         — list semua override
  PUT    /organizations/{org_id}/direct-income-overrides/{expense_category_id}  — upsert override
  DELETE /organizations/{org_id}/direct-income-overrides/{expense_category_id}  — hapus override (kembali ke otomatis)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import get_org_access
from ..database import get_db
from ..crud import direct_income_override as crud
from ..crud import organization as org_crud
from ..crud import expense_category as exp_crud
from ..schemas.direct_income_override import DirectIncomeOverrideUpsert, DirectIncomeOverrideRead

router = APIRouter(
    prefix="/organizations/{org_id}/direct-income-overrides",
    tags=["Direct Income Overrides"],
    dependencies=[Depends(get_org_access)],
)


def _get_org_or_404(db: Session, org_id: int):
    org = org_crud.get(db, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.get("", response_model=list[DirectIncomeOverrideRead])
def list_overrides(org_id: int, db: Session = Depends(get_db)):
    """Ambil semua override direct income untuk suatu organisasi."""
    _get_org_or_404(db, org_id)
    return crud.list_by_org(db, org_id)


@router.put(
    "/{expense_category_id}",
    response_model=DirectIncomeOverrideRead,
    summary="Upsert override nilai direct income untuk expense category tertentu",
)
def upsert_override(
    org_id: int,
    expense_category_id: int,
    data: DirectIncomeOverrideUpsert,
    db: Session = Depends(get_db),
):
    _get_org_or_404(db, org_id)
    exp_cat = exp_crud.get(db, expense_category_id)
    if exp_cat is None:
        raise HTTPException(status_code=404, detail="Expense category not found")
    if not exp_cat.is_direct_income:
        raise HTTPException(
            status_code=422,
            detail="Expense category is not marked as direct income",
        )
    return crud.upsert(db, org_id, expense_category_id, data)


@router.delete(
    "/{expense_category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Hapus override — nilai kembali ke otomatis dari budget entry",
)
def delete_override(org_id: int, expense_category_id: int, db: Session = Depends(get_db)):
    _get_org_or_404(db, org_id)
    obj = crud.get_by_org_and_expense(db, org_id, expense_category_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Override not found")
    crud.delete(db, obj)
