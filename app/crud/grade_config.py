"""
CRUD untuk GradeConfig.

Menggunakan pola upsert: jika baris sudah ada untuk org_id maka diperbarui,
jika belum ada maka dibuat baru. Hanya satu konfigurasi grade per organisasi.
"""
from sqlalchemy.orm import Session

from ..models.grade_config import GradeConfig
from ..schemas.grade_config import GradeConfigCreate, GradeConfigUpdate


def get(db: Session, org_id: int) -> GradeConfig | None:
    """Ambil konfigurasi grade untuk suatu organisasi.

    Args:
        db: Database session.
        org_id: ID organisasi.

    Returns:
        GradeConfig jika ditemukan, None jika belum dikonfigurasi.
    """
    return db.query(GradeConfig).filter(GradeConfig.organization_id == org_id).first()


def upsert(db: Session, org_id: int, data: GradeConfigCreate | GradeConfigUpdate) -> GradeConfig:
    """Buat atau perbarui konfigurasi grade untuk suatu organisasi.

    Args:
        db: Database session.
        org_id: ID organisasi.
        data: Data konfigurasi grade baru.

    Returns:
        Instance GradeConfig yang sudah disimpan.
    """
    obj = get(db, org_id)
    if obj is None:
        obj = GradeConfig(organization_id=org_id, **data.model_dump())
        db.add(obj)
    else:
        for key, value in data.model_dump().items():
            setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, org_id: int) -> bool:
    """Hapus konfigurasi grade untuk suatu organisasi.

    Args:
        db: Database session.
        org_id: ID organisasi.

    Returns:
        True jika berhasil dihapus, False jika tidak ditemukan.
    """
    obj = get(db, org_id)
    if obj is None:
        return False
    db.delete(obj)
    db.commit()
    return True
