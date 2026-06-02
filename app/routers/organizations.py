"""
Router organisasi — CRUD untuk entitas Organization.

Endpoint:
  GET    /organizations              — daftar semua organisasi (login wajib)
  POST   /organizations              — buat organisasi baru + user otomatis (admin only)
  GET    /organizations/{org_id}     — detail organisasi + daftar anak langsung (login wajib)
  PUT    /organizations/{org_id}     — update nama/kota/parent (admin only)
  DELETE /organizations/{org_id}     — hapus organisasi (admin only)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import generate_random_password, get_current_user, require_admin
from ..crud import organization as crud
from ..crud.user import create_user
from ..database import get_db
from ..models.user import UserRole
from ..schemas.organization import (
    OrganizationCreate,
    OrganizationCreated,
    OrganizationRead,
    OrganizationReadWithChildren,
    OrganizationUpdate,
)

router = APIRouter(prefix="/organizations", tags=["Organizations"])


def _get_or_404(db: Session, org_id: int):
    obj = crud.get(db, org_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return obj


@router.get("", response_model=list[OrganizationRead])
def list_organizations(
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Daftar organisasi.

    ADMIN melihat semua organisasi. User ORG hanya melihat organisasinya
    sendiri beserta seluruh organisasi yang dinaunginya secara berjenjang.
    """
    if current_user.role == UserRole.ADMIN:
        return crud.get_all(db, skip=skip, limit=limit)
    if current_user.org_id is None:
        return []
    subtree = crud.get_subtree(db, current_user.org_id)
    return subtree[skip : skip + limit]


@router.post("", response_model=OrganizationCreated, status_code=status.HTTP_201_CREATED)
def create_organization(
    data: OrganizationCreate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """
    Buat organisasi baru (admin only).

    Secara otomatis membuat user login untuk organisasi ini dengan password
    acak. Password dikembalikan sekali dalam response — simpan baik-baik.
    Password bisa direset via POST /organizations/{org_id}/reset-password.
    """
    if crud.get_by_code(db, data.code):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Kode organisasi sudah ada")
    org = crud.create(db, data)

    # Auto-create login user untuk org ini
    plain_password = generate_random_password()
    create_user(
        db,
        username=org.code.lower(),
        plain_password=plain_password,
        role=UserRole.ORG,
        org_id=org.id,
    )

    return OrganizationCreated(
        **OrganizationRead.model_validate(org).model_dump(),
        generated_password=plain_password,
    )


@router.get("/{org_id}", response_model=OrganizationReadWithChildren)
def get_organization(
    org_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Detail organisasi beserta daftar anak langsungnya.

    User ORG hanya boleh mengakses organisasinya sendiri atau organisasi yang
    dinaunginya secara berjenjang; selain itu dikembalikan 403.
    """
    obj = _get_or_404(db, org_id)
    if current_user.role != UserRole.ADMIN:
        if current_user.org_id is None or org_id not in crud.get_descendant_ids(
            db, current_user.org_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tidak punya akses ke organisasi ini",
            )
    return obj


@router.put("/{org_id}", response_model=OrganizationRead)
def update_organization(
    org_id: int,
    data: OrganizationUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    obj = _get_or_404(db, org_id)
    return crud.update(db, obj, data)


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organization(
    org_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    obj = _get_or_404(db, org_id)
    crud.delete(db, obj)
