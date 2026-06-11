"""
Utilitas autentikasi: hashing password, pembuatan/validasi JWT,
dan FastAPI dependencies untuk proteksi endpoint.

Dependencies yang diekspor:
- get_current_user: Requires valid JWT, returns User.
- require_admin: Requires ADMIN role.
- get_org_access: Requires login + akses ke org_id dari path (admin atau pemilik org).
"""
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models.user import User, UserRole

_ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ── Password utilities ─────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Hash password menggunakan bcrypt."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verifikasi password plaintext terhadap hash yang tersimpan."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def generate_random_password(length: int = 12) -> str:
    """
    Generate password acak yang aman untuk akun organisasi.

    Args:
        length: Panjang password yang dihasilkan (default 12).

    Returns:
        String password acak berisi huruf dan angka.
    """
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


# ── JWT utilities ──────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Buat JWT access token.

    Args:
        data: Payload yang akan di-encode ke token (wajib ada 'sub').
        expires_delta: Override masa berlaku token; default dari settings.

    Returns:
        JWT token string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=_ALGORITHM)


# ── FastAPI dependencies ───────────────────────────────────────────────────────

def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency — validasi JWT dan kembalikan user yang sedang login.

    Raises:
        HTTPException 401: Token tidak valid atau user tidak ditemukan.
        HTTPException 403: Akun dinonaktifkan.
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token tidak valid atau sudah kedaluwarsa",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[_ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exc
    except InvalidTokenError:
        raise credentials_exc

    # Lazy import to avoid circular dependency (crud.user imports hash_password from here)
    from .crud.user import get_by_username
    user = get_by_username(db, username)
    if user is None:
        raise credentials_exc
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun dinonaktifkan",
        )
    return user


def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    FastAPI dependency — hanya izinkan user dengan role ADMIN.

    Raises:
        HTTPException 403: User bukan admin.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses hanya untuk admin",
        )
    return current_user


def require_not_locked(
    org_id: int,
    db: Session = Depends(get_db),
) -> None:
    """
    FastAPI dependency — blokir operasi tulis jika budget organisasi sudah dikunci.

    Raises:
        HTTPException 423: Budget organisasi telah dikunci.
    """
    from .crud import organization as org_crud
    org = org_crud.get(db, org_id)
    if org and org.is_locked:
        locked_by = org.locked_by_username or "pengguna tidak diketahui"
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Budget organisasi ini telah dikunci oleh {locked_by}",
        )


def get_org_access(
    org_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency — izinkan admin atau organisasi yang menaungi org_id.

    Akses berlaku secara berjenjang: organisasi yang lebih tinggi boleh
    mengakses semua organisasi yang dinaunginya sampai ke bawah. Contohnya
    PUSAT dapat mengakses seluruh CABANG dan UNIT di bawahnya, dan CABANG
    dapat mengakses seluruh UNIT di bawahnya.

    Mengambil org_id dari path parameter secara otomatis oleh FastAPI.

    Args:
        org_id: ID organisasi dari path parameter.
        current_user: User yang sedang login.
        db: Session database.

    Raises:
        HTTPException 403: User ORG mencoba mengakses org di luar naungannya.
    """
    if current_user.role == UserRole.ADMIN:
        return current_user
    if current_user.org_id is not None:
        # Lazy import to avoid circular dependency at module load time.
        from .crud import organization as org_crud
        allowed_ids = org_crud.get_descendant_ids(db, current_user.org_id)
        if org_id in allowed_ids:
            return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Tidak punya akses ke organisasi ini",
    )
