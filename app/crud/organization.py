"""
CRUD untuk entitas Organization.

Fungsi `get_by_code` menggunakan kode uppercase agar pencarian case-insensitive.
Fungsi `create` dan `update` menerima schema Pydantic dan melakukan commit+refresh.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models.organization import Organization
from ..schemas.organization import OrganizationCreate, OrganizationUpdate


def get(db: Session, org_id: int) -> Organization | None:
    return db.get(Organization, org_id)


def get_by_code(db: Session, code: str) -> Organization | None:
    return db.query(Organization).filter(Organization.code == code.upper()).first()


def get_all(db: Session, skip: int = 0, limit: int = 200) -> list[Organization]:
    return db.query(Organization).offset(skip).limit(limit).all()


def get_descendant_ids(db: Session, org_id: int, include_self: bool = True) -> set[int]:
    """
    Kumpulkan id organisasi `org_id` beserta seluruh turunannya secara berjenjang.

    Misal PUSAT → mencakup semua CABANG di bawahnya dan semua UNIT di bawah
    tiap CABANG. Digunakan untuk akses berjenjang: organisasi yang lebih tinggi
    boleh melihat semua organisasi yang dinaunginya.

    Args:
        db: Session database.
        org_id: ID organisasi akar.
        include_self: Sertakan `org_id` itu sendiri di hasil (default True).

    Returns:
        Set berisi id organisasi akar (opsional) dan semua keturunannya.
    """
    # Ambil seluruh edge parent→child sekali, lalu telusuri secara iteratif.
    edges = db.query(Organization.id, Organization.parent_id).all()
    children_map: dict[int | None, list[int]] = {}
    for child_id, parent_id in edges:
        children_map.setdefault(parent_id, []).append(child_id)

    result: set[int] = {org_id} if include_self else set()
    stack = [org_id]
    while stack:
        current = stack.pop()
        for child_id in children_map.get(current, []):
            if child_id not in result:
                result.add(child_id)
                stack.append(child_id)
    return result


def get_subtree(db: Session, org_id: int) -> list[Organization]:
    """Kembalikan organisasi `org_id` dan seluruh turunannya secara berjenjang."""
    ids = get_descendant_ids(db, org_id, include_self=True)
    if not ids:
        return []
    return db.query(Organization).filter(Organization.id.in_(ids)).all()


def create(db: Session, data: OrganizationCreate) -> Organization:
    obj = Organization(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, org: Organization, data: OrganizationUpdate) -> Organization:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(org, key, value)
    db.commit()
    db.refresh(org)
    return org


def delete(db: Session, org: Organization) -> None:
    db.delete(org)
    db.commit()


def lock(db: Session, org: Organization, user_id: int, username: str) -> Organization:
    """Kunci budget organisasi. Catat siapa yang mengunci dan kapan."""
    org.is_locked = True
    org.locked_at = datetime.now(timezone.utc)
    org.locked_by_user_id = user_id
    org.locked_by_username = username
    db.commit()
    db.refresh(org)
    return org


def unlock(db: Session, org: Organization) -> Organization:
    """Buka kunci budget organisasi."""
    org.is_locked = False
    org.locked_at = None
    org.locked_by_user_id = None
    org.locked_by_username = None
    db.commit()
    db.refresh(org)
    return org
