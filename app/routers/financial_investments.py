"""
Router investasi keuangan CABANG/PUSAT — CRUD untuk FinancialInvestment.

Endpoint:
  GET    /organizations/{org_id}/financial-investments              — daftar investasi
  POST   /organizations/{org_id}/financial-investments              — tambah investasi
  PUT    /organizations/{org_id}/financial-investments/{inv_id}     — update
  DELETE /organizations/{org_id}/financial-investments/{inv_id}     — hapus

Validasi: operasi POST/PUT/DELETE hanya diizinkan untuk org CABANG atau PUSAT.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import get_org_access, require_not_locked
from ..database import get_db
from ..crud import financial_investment as crud
from ..crud import organization as org_crud
from ..models.organization import OrgType
from ..schemas.financial_investment import (
    FinancialInvestmentCreate,
    FinancialInvestmentUpdate,
    FinancialInvestmentRead,
)

router = APIRouter(
    prefix="/organizations/{org_id}/financial-investments",
    tags=["Financial Investments"],
    dependencies=[Depends(get_org_access)],
)


def _get_org_or_404(db: Session, org_id: int):
    org = org_crud.get(db, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


def _require_cabang_or_pusat(org):
    if org.org_type == OrgType.UNIT:
        raise HTTPException(
            status_code=403,
            detail="Investasi keuangan hanya dapat dikelola oleh CABANG atau PUSAT.",
        )


@router.get("", response_model=list[FinancialInvestmentRead])
def list_financial_investments(org_id: int, db: Session = Depends(get_db)):
    _get_org_or_404(db, org_id)
    return crud.list_by_org(db, org_id)


@router.post(
    "", response_model=FinancialInvestmentRead, status_code=status.HTTP_201_CREATED
)
def create_financial_investment(
    org_id: int,
    data: FinancialInvestmentCreate,
    db: Session = Depends(get_db),
    _=Depends(require_not_locked),
):
    org = _get_org_or_404(db, org_id)
    _require_cabang_or_pusat(org)
    return crud.create(db, org_id, data)


@router.put("/{inv_id}", response_model=FinancialInvestmentRead)
def update_financial_investment(
    org_id: int,
    inv_id: int,
    data: FinancialInvestmentUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_not_locked),
):
    org = _get_org_or_404(db, org_id)
    _require_cabang_or_pusat(org)
    inv = crud.get(db, inv_id)
    if inv is None or inv.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Financial investment not found")
    return crud.update(db, inv, data)


@router.delete("/{inv_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_financial_investment(
    org_id: int,
    inv_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_not_locked),
):
    org = _get_org_or_404(db, org_id)
    _require_cabang_or_pusat(org)
    inv = crud.get(db, inv_id)
    if inv is None or inv.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Financial investment not found")
    crud.delete(db, inv)
