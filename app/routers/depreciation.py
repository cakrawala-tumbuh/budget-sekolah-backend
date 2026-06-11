"""
Router aset tetap lama yang masih disusutkan — CRUD untuk DepreciationOldAsset.

Mengelola Tabel B pada sheet Depresiasi template RAB Unit.
Endpoint:
  GET    /organizations/{org_id}/depreciation              — semua aset lama
  POST   /organizations/{org_id}/depreciation              — tambah aset lama
  PUT    /organizations/{org_id}/depreciation/{dep_id}     — update aset
  DELETE /organizations/{org_id}/depreciation/{dep_id}     — hapus aset
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import get_org_access, require_not_locked
from ..database import get_db
from ..config import settings
from ..crud import misc as crud, organization as org_crud
from ..schemas.depreciation import (
    DepreciationOldAssetCreate, DepreciationOldAssetUpdate, DepreciationOldAssetRead
)
from ..models.depreciation import DepreciationOldAsset

router = APIRouter(
    prefix="/organizations/{org_id}/depreciation",
    tags=["Depreciation"],
    dependencies=[Depends(get_org_access)],
)


def _get_org_or_404(db: Session, org_id: int):
    org = org_crud.get(db, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


def _enrich(dep: DepreciationOldAsset, fiscal_year: int) -> DepreciationOldAssetRead:
    return DepreciationOldAssetRead(
        id=dep.id,
        organization_id=dep.organization_id,
        asset_code=dep.asset_code,
        asset_name=dep.asset_name,
        acquisition_cost=dep.acquisition_cost,
        useful_life=dep.useful_life,
        acquisition_year=dep.acquisition_year,
        dep_per_year=dep.dep_per_year(),
        dep_current_year=dep.dep_current_year(fiscal_year),
        book_value=dep.book_value(fiscal_year),
        created_at=dep.created_at,
        updated_at=dep.updated_at,
    )


@router.get("", response_model=list[DepreciationOldAssetRead])
def list_old_assets(org_id: int, db: Session = Depends(get_db)):
    _get_org_or_404(db, org_id)
    fiscal_year = int(settings.budget_year.split("-")[0])
    return [_enrich(d, fiscal_year) for d in crud.list_dep_by_org(db, org_id)]


@router.post("", response_model=DepreciationOldAssetRead, status_code=status.HTTP_201_CREATED)
def add_old_asset(org_id: int, data: DepreciationOldAssetCreate, db: Session = Depends(get_db), _=Depends(require_not_locked)):
    _get_org_or_404(db, org_id)
    fiscal_year = int(settings.budget_year.split("-")[0])
    dep = crud.create_dep(db, org_id, data)
    return _enrich(dep, fiscal_year)


@router.put("/{dep_id}", response_model=DepreciationOldAssetRead)
def update_old_asset(org_id: int, dep_id: int, data: DepreciationOldAssetUpdate, db: Session = Depends(get_db), _=Depends(require_not_locked)):
    _get_org_or_404(db, org_id)
    dep = crud.get_dep(db, dep_id)
    if dep is None or dep.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Asset not found")
    dep = crud.update_dep(db, dep, data)
    fiscal_year = int(settings.budget_year.split("-")[0])
    return _enrich(dep, fiscal_year)


@router.delete("/{dep_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_old_asset(org_id: int, dep_id: int, db: Session = Depends(get_db), _=Depends(require_not_locked)):
    _get_org_or_404(db, org_id)
    dep = crud.get_dep(db, dep_id)
    if dep is None or dep.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Asset not found")
    crud.delete_dep(db, dep)
