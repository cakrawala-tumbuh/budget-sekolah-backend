"""
Fungsi CRUD untuk entitas User.

Tidak ada logika bisnis di sini — hanya operasi database.
Hash password dilakukan di auth.py sebelum memanggil fungsi ini.
"""
from sqlalchemy.orm import Session

from ..models.user import User, UserRole
from ..auth import hash_password


def get_by_username(db: Session, username: str) -> User | None:
    """
    Ambil user berdasarkan username.

    Args:
        db: Sesi database.
        username: Nama pengguna yang dicari.

    Returns:
        Instance User jika ditemukan, None jika tidak.
    """
    return db.query(User).filter(User.username == username).first()


def get_by_org_id(db: Session, org_id: int) -> User | None:
    """
    Ambil user yang terkait dengan organisasi tertentu.

    Args:
        db: Sesi database.
        org_id: ID organisasi.

    Returns:
        Instance User jika ditemukan, None jika tidak.
    """
    return db.query(User).filter(User.org_id == org_id).first()


def get_all(db: Session) -> list[User]:
    """
    Ambil semua user.

    Args:
        db: Sesi database.

    Returns:
        Daftar semua User.
    """
    return db.query(User).all()


def create_user(
    db: Session,
    username: str,
    plain_password: str,
    role: UserRole,
    org_id: int | None = None,
) -> User:
    """
    Buat user baru dengan password yang di-hash.

    Args:
        db: Sesi database.
        username: Nama pengguna unik.
        plain_password: Password plaintext yang akan di-hash.
        role: Role user (ADMIN atau ORG).
        org_id: ID organisasi, hanya untuk role ORG.

    Returns:
        Instance User yang baru dibuat.
    """
    user = User(
        username=username,
        hashed_password=hash_password(plain_password),
        role=role,
        org_id=org_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_password(db: Session, user: User, plain_password: str) -> User:
    """
    Update password user dengan password baru.

    Args:
        db: Sesi database.
        user: Instance User yang akan diupdate.
        plain_password: Password baru dalam bentuk plaintext.

    Returns:
        Instance User setelah diupdate.
    """
    user.hashed_password = hash_password(plain_password)
    db.commit()
    db.refresh(user)
    return user


def create_or_update_admin(db: Session, plain_password: str) -> User:
    """
    Buat atau perbarui akun admin.

    Dipanggil saat startup untuk memastikan akun admin selalu sinkron
    dengan ADMIN_PASSWORD di environment.

    Args:
        db: Sesi database.
        plain_password: Password admin dari konfigurasi.

    Returns:
        Instance User admin.
    """
    user = get_by_username(db, "admin")
    if user is None:
        return create_user(db, "admin", plain_password, UserRole.ADMIN)
    return update_password(db, user, plain_password)
