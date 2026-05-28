"""
Router autentikasi.

Endpoint:
  POST /auth/login  — login dengan username + password, kembalikan JWT token
  GET  /auth/me     — info user yang sedang login
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..auth import create_access_token, get_current_user, verify_password
from ..crud.user import get_by_username
from ..database import get_db
from ..schemas.auth import Token, UserRead

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Login dengan username dan password, kembalikan JWT access token.

    Args:
        form_data: Form OAuth2 berisi username dan password.
        db: Sesi database.

    Returns:
        JWT access token dan token type.

    Raises:
        HTTPException 401: Username atau password salah.
        HTTPException 403: Akun dinonaktifkan.
    """
    user = get_by_username(db, form_data.username)
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun dinonaktifkan",
        )
    token = create_access_token({"sub": user.username})
    return Token(access_token=token)


@router.get("/me", response_model=UserRead)
def me(current_user=Depends(get_current_user)):
    """
    Kembalikan informasi user yang sedang login.

    Returns:
        Data user saat ini (tanpa password).
    """
    return current_user
