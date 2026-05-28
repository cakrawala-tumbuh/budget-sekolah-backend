"""
Router pembelian aset tetap baru — CRUD untuk Investment.

Endpoint:
  GET    /organizations/{org_id}/investments              — semua aset baru
  POST   /organizations/{org_id}/investments              — tambah aset baru
  PUT    /organizations/{org_id}/investments/{inv_id}     — update aset
  DELETE /organizations/{org_id}/investments/{inv_id}     — hapus aset
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import get_org_access
from ..database import get_db
from ..crud import investment as crud, organization as org_crud
from ..crud import investment_category as inv_cat_crud
from ..schemas.investment import InvestmentCreate, InvestmentUpdate, InvestmentRead

router = APIRouter(
    prefix="/organizations/{org_id}/investments",
    tags=["Investments"],
    dependencies=[Depends(get_org_access)],
)


def _get_org_or_404(db: Session, org_id: int):
    org = org_crud.get(db, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.get("", response_model=list[InvestmentRead])
def list_investments(org_id: int, db: Session = Depends(get_db)):
    _get_org_or_404(db, org_id)
    return crud.list_by_org(db, org_id)


@router.post("", response_model=InvestmentRead, status_code=status.HTTP_201_CREATED)
def create_investment(org_id: int, data: InvestmentCreate, db: Session = Depends(get_db)):
    _get_org_or_404(db, org_id)
    if inv_cat_crud.get(db, data.investment_category_id) is None:
        raise HTTPException(status_code=422, detail="investment_category_id not found")
    return crud.create(db, org_id, data)


@router.put("/{inv_id}", response_model=InvestmentRead)
def update_investment(org_id: int, inv_id: int, data: InvestmentUpdate, db: Session = Depends(get_db)):
    _get_org_or_404(db, org_id)
    inv = crud.get(db, inv_id)
    if inv is None or inv.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Investment not found")
    return crud.update(db, inv, data)


@router.delete("/{inv_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_investment(org_id: int, inv_id: int, db: Session = Depends(get_db)):
    _get_org_or_404(db, org_id)
    inv = crud.get(db, inv_id)
    if inv is None or inv.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Investment not found")
    crud.delete(db, inv)
