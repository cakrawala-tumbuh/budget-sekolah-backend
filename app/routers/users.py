"""
Router manajemen user (khusus admin).

Endpoint:
  GET  /users                                  — daftar semua user
  POST /organizations/{org_id}/reset-password  — reset password user org, kembalikan password baru
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import generate_random_password, require_admin
from ..crud import organization as org_crud
from ..crud import user as user_crud
from ..database import get_db
from ..schemas.auth import PasswordResetResponse, UserRead

router = APIRouter(tags=["Users"])


@router.get("/users", response_model=list[UserRead])
def list_users(
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Daftar semua user (admin only).

    Returns:
        List semua user terdaftar.
    """
    return user_crud.get_all(db)


@router.post(
    "/organizations/{org_id}/reset-password",
    response_model=PasswordResetResponse,
)
def reset_org_password(
    org_id: int,
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Reset password user untuk organisasi tertentu (admin only).

    Password baru di-generate secara acak dan dikembalikan sekali.
    Simpan password ini karena tidak bisa dilihat lagi setelah ini.

    Args:
        org_id: ID organisasi yang passwordnya akan direset.

    Returns:
        Username dan password baru yang sudah di-generate.

    Raises:
        HTTPException 404: Organisasi atau user tidak ditemukan.
    """
    org = org_crud.get(db, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")

    user = user_crud.get_by_org_id(db, org_id)
    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User untuk organisasi ini tidak ditemukan",
        )

    new_password = generate_random_password()
    user_crud.update_password(db, user, new_password)

    return PasswordResetResponse(username=user.username, new_password=new_password)
