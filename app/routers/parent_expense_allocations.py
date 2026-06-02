"""
Router untuk konfigurasi alokasi biaya dari Cabang/Pusat ke unit-unit anak
(ParentExpenseAllocation).

Endpoint:
  GET    /organizations/{org_id}/parent-expense-allocations
  POST   /organizations/{org_id}/parent-expense-allocations
  PATCH  /organizations/{org_id}/parent-expense-allocations/{alloc_id}
  DELETE /organizations/{org_id}/parent-expense-allocations/{alloc_id}

Hanya organisasi bertipe CABANG atau PUSAT yang dapat memiliki konfigurasi ini.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..auth import get_org_access
from ..database import get_db
from ..crud import organization as org_crud
from ..crud import parent_expense_allocation as crud
from ..models.organization import OrgType
from ..schemas.parent_expense_allocation import (
    CopyResult,
    ParentExpenseAllocationCreate,
    ParentExpenseAllocationRead,
    ParentExpenseAllocationUpdate,
)

router = APIRouter(
    tags=["Parent Expense Allocations"],
    dependencies=[Depends(get_org_access)],
)


def _get_parent_org_or_404(db: Session, org_id: int):
    """Ambil organisasi dan pastikan bertipe CABANG atau PUSAT."""
    org = org_crud.get(db, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    if org.org_type == OrgType.UNIT:
        raise HTTPException(
            status_code=422,
            detail="Parent expense allocations can only be configured for CABANG or PUSAT organizations",
        )
    return org


def _read(alloc) -> ParentExpenseAllocationRead:
    cat = alloc.expense_category
    return ParentExpenseAllocationRead(
        id=alloc.id,
        parent_org_id=alloc.parent_org_id,
        expense_category_id=alloc.expense_category_id,
        affects_up=alloc.affects_up,
        is_active=alloc.is_active,
        expense_category_code=cat.code if cat else None,
        expense_category_label=cat.label if cat else None,
    )


@router.get(
    "/organizations/{org_id}/parent-expense-allocations",
    response_model=list[ParentExpenseAllocationRead],
    summary="Daftar konfigurasi alokasi biaya induk ke anak",
)
def list_allocations(org_id: int, db: Session = Depends(get_db)):
    """Kembalikan semua konfigurasi alokasi biaya dari organisasi induk ini ke unit anaknya."""
    _get_parent_org_or_404(db, org_id)
    allocs = crud.list_by_org(db, org_id)
    return [_read(a) for a in allocs]


@router.post(
    "/organizations/{org_id}/parent-expense-allocations",
    response_model=ParentExpenseAllocationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Tambah konfigurasi alokasi biaya induk ke anak",
)
def create_allocation(
    org_id: int,
    data: ParentExpenseAllocationCreate,
    db: Session = Depends(get_db),
):
    """
    Daftarkan kategori biaya tertentu dari organisasi induk untuk dialokasikan
    ke unit-unit anaknya. Setiap pasangan (org, expense_category) harus unik.
    """
    _get_parent_org_or_404(db, org_id)
    try:
        alloc = crud.create(db, org_id, data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Allocation for this expense category already exists for this organization",
        )
    return _read(alloc)


@router.patch(
    "/organizations/{org_id}/parent-expense-allocations/{alloc_id}",
    response_model=ParentExpenseAllocationRead,
    summary="Perbarui konfigurasi alokasi biaya induk",
)
def update_allocation(
    org_id: int,
    alloc_id: int,
    data: ParentExpenseAllocationUpdate,
    db: Session = Depends(get_db),
):
    _get_parent_org_or_404(db, org_id)
    alloc = crud.get(db, alloc_id)
    if alloc is None or alloc.parent_org_id != org_id:
        raise HTTPException(status_code=404, detail="Allocation not found")
    alloc = crud.update(db, alloc, data)
    return _read(alloc)


@router.delete(
    "/organizations/{org_id}/parent-expense-allocations/{alloc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Hapus konfigurasi alokasi biaya induk",
)
def delete_allocation(
    org_id: int,
    alloc_id: int,
    db: Session = Depends(get_db),
):
    _get_parent_org_or_404(db, org_id)
    alloc = crud.get(db, alloc_id)
    if alloc is None or alloc.parent_org_id != org_id:
        raise HTTPException(status_code=404, detail="Allocation not found")
    crud.delete(db, alloc)


@router.post(
    "/organizations/{org_id}/parent-expense-allocations/copy-from/{source_org_id}",
    response_model=CopyResult,
    summary="Salin konfigurasi alokasi biaya dari organisasi lain",
)
def copy_allocations_from(
    org_id: int,
    source_org_id: int,
    affects_up: bool | None = Query(None),
    db: Session = Depends(get_db),
):
    """
    Salin konfigurasi kategori biaya dari organisasi lain ke organisasi ini.
    Kategori yang sudah ada di tujuan akan dilewati (tidak digandakan).
    Gunakan query param affects_up=true/false untuk filter hanya UP atau US.
    """
    _get_parent_org_or_404(db, org_id)
    _get_parent_org_or_404(db, source_org_id)
    if org_id == source_org_id:
        raise HTTPException(status_code=400, detail="Source and target organization must be different")
    return crud.copy_from(db, org_id, source_org_id, affects_up)
