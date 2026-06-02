"""
Router untuk subsidi dari Cabang/Pusat ke unit penerima (Subsidy).

Endpoint:
  GET    /organizations/{org_id}/subsidies
  POST   /organizations/{org_id}/subsidies
  PATCH  /organizations/{org_id}/subsidies/{subsidy_id}
  DELETE /organizations/{org_id}/subsidies/{subsidy_id}

Aturan keterhubungan:
  - CABANG hanya dapat memberi subsidi ke UNIT anaknya.
  - PUSAT dapat memberi subsidi ke CABANG atau UNIT mana pun.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import get_org_access
from ..database import get_db
from ..crud import organization as org_crud
from ..crud import subsidy as crud
from ..models.organization import OrgType, Organization
from ..schemas.subsidy import SubsidyCreate, SubsidyRead, SubsidyUpdate

router = APIRouter(
    tags=["Subsidies"],
    dependencies=[Depends(get_org_access)],
)


def _get_provider_or_404(db: Session, org_id: int) -> Organization:
    """Ambil organisasi pemberi dan pastikan bertipe CABANG atau PUSAT."""
    org = org_crud.get(db, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    if org.org_type == OrgType.UNIT:
        raise HTTPException(
            status_code=422,
            detail="Subsidi hanya dapat diberikan oleh organisasi CABANG atau PUSAT",
        )
    return org


def _validate_recipient(db: Session, provider: Organization, recipient_org_id: int) -> Organization:
    """
    Pastikan organisasi penerima valid sesuai aturan:
      - CABANG → UNIT anaknya (parent_id == provider.id).
      - PUSAT  → CABANG atau UNIT mana pun (bukan dirinya, bukan PUSAT lain).
    """
    recipient = org_crud.get(db, recipient_org_id)
    if recipient is None:
        raise HTTPException(status_code=404, detail="Organisasi penerima tidak ditemukan")
    if recipient.id == provider.id:
        raise HTTPException(status_code=422, detail="Penerima tidak boleh organisasi pemberi sendiri")

    if provider.org_type == OrgType.CABANG:
        if recipient.org_type != OrgType.UNIT or recipient.parent_id != provider.id:
            raise HTTPException(
                status_code=422,
                detail="CABANG hanya dapat memberi subsidi ke UNIT anaknya",
            )
    else:  # PUSAT
        if recipient.org_type == OrgType.PUSAT:
            raise HTTPException(
                status_code=422,
                detail="PUSAT hanya dapat memberi subsidi ke CABANG atau UNIT",
            )
    return recipient


def _read(s) -> SubsidyRead:
    return SubsidyRead(
        id=s.id,
        provider_org_id=s.provider_org_id,
        recipient_org_id=s.recipient_org_id,
        expense_category_id=s.expense_category_id,
        income_category_id=s.income_category_id,
        amount=s.amount,
        is_active=s.is_active,
        recipient_org_name=s.recipient_org.name if s.recipient_org else None,
        expense_category_code=s.expense_category.code if s.expense_category else None,
        expense_category_label=s.expense_category.label if s.expense_category else None,
        income_category_code=s.income_category.code if s.income_category else None,
        income_category_label=s.income_category.label if s.income_category else None,
    )


@router.get(
    "/organizations/{org_id}/subsidies",
    response_model=list[SubsidyRead],
    summary="Daftar subsidi dari organisasi ini ke penerima",
)
def list_subsidies(org_id: int, db: Session = Depends(get_db)):
    _get_provider_or_404(db, org_id)
    return [_read(s) for s in crud.list_by_provider(db, org_id)]


@router.post(
    "/organizations/{org_id}/subsidies",
    response_model=SubsidyRead,
    status_code=status.HTTP_201_CREATED,
    summary="Tambah subsidi ke penerima",
)
def create_subsidy(org_id: int, data: SubsidyCreate, db: Session = Depends(get_db)):
    provider = _get_provider_or_404(db, org_id)
    _validate_recipient(db, provider, data.recipient_org_id)
    subsidy = crud.create(db, org_id, data)
    return _read(subsidy)


@router.patch(
    "/organizations/{org_id}/subsidies/{subsidy_id}",
    response_model=SubsidyRead,
    summary="Perbarui subsidi",
)
def update_subsidy(
    org_id: int, subsidy_id: int, data: SubsidyUpdate, db: Session = Depends(get_db)
):
    provider = _get_provider_or_404(db, org_id)
    subsidy = crud.get(db, subsidy_id)
    if subsidy is None or subsidy.provider_org_id != org_id:
        raise HTTPException(status_code=404, detail="Subsidi tidak ditemukan")
    if data.recipient_org_id is not None:
        _validate_recipient(db, provider, data.recipient_org_id)
    subsidy = crud.update(db, subsidy, data)
    return _read(subsidy)


@router.delete(
    "/organizations/{org_id}/subsidies/{subsidy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Hapus subsidi",
)
def delete_subsidy(org_id: int, subsidy_id: int, db: Session = Depends(get_db)):
    _get_provider_or_404(db, org_id)
    subsidy = crud.get(db, subsidy_id)
    if subsidy is None or subsidy.provider_org_id != org_id:
        raise HTTPException(status_code=404, detail="Subsidi tidak ditemukan")
    crud.delete(db, subsidy)
