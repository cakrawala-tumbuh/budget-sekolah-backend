"""
Router untuk konfigurasi grade satuan pendidikan.

Endpoint:
  GET    /organizations/{org_id}/grade-config  — Ambil konfigurasi grade
  PUT    /organizations/{org_id}/grade-config  — Buat atau perbarui konfigurasi
  DELETE /organizations/{org_id}/grade-config  — Hapus konfigurasi (kembali ke default)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import get_org_access
from ..database import get_db
from ..crud import grade_config as crud, organization as org_crud
from ..models.organization import OrgType
from ..schemas.grade_config import GradeConfigCreate, GradeConfigRead

router = APIRouter(
    prefix="/organizations/{org_id}/grade-config",
    tags=["Grade Config"],
    dependencies=[Depends(get_org_access)],
)


def _get_unit_or_404(db: Session, org_id: int):
    org = org_crud.get(db, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    if org.org_type != OrgType.UNIT:
        raise HTTPException(
            status_code=422,
            detail="Konfigurasi grade hanya berlaku untuk organisasi bertipe UNIT",
        )
    return org


@router.get("", response_model=GradeConfigRead)
def get_grade_config(org_id: int, db: Session = Depends(get_db)):
    """Ambil konfigurasi grade untuk satuan pendidikan.

    Mengembalikan 404 jika konfigurasi belum pernah disimpan.
    """
    _get_unit_or_404(db, org_id)
    obj = crud.get(db, org_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Konfigurasi grade belum diisi")
    return GradeConfigRead.from_orm_with_labels(obj)


@router.put("", response_model=GradeConfigRead)
def upsert_grade_config(
    org_id: int, data: GradeConfigCreate, db: Session = Depends(get_db)
):
    """Buat atau perbarui konfigurasi grade satuan pendidikan.

    Jika konfigurasi sudah ada maka diperbarui, jika belum maka dibuat baru.
    """
    _get_unit_or_404(db, org_id)
    obj = crud.upsert(db, org_id, data)
    return GradeConfigRead.from_orm_with_labels(obj)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_grade_config(org_id: int, db: Session = Depends(get_db)):
    """Hapus konfigurasi grade satuan pendidikan.

    Setelah dihapus, asumsi kembali ke default 6 grade dengan label "Kelas 1"–"Kelas 6".
    """
    _get_unit_or_404(db, org_id)
    if not crud.delete(db, org_id):
        raise HTTPException(status_code=404, detail="Konfigurasi grade belum diisi")
