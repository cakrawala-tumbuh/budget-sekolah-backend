"""
CRUD untuk entitas Organization.

Fungsi `get_by_code` menggunakan kode uppercase agar pencarian case-insensitive.
Fungsi `create` dan `update` menerima schema Pydantic dan melakukan commit+refresh.
"""
from sqlalchemy.orm import Session

from ..models.organization import Organization
from ..schemas.organization import OrganizationCreate, OrganizationUpdate


def get(db: Session, org_id: int) -> Organization | None:
    return db.get(Organization, org_id)


def get_by_code(db: Session, code: str) -> Organization | None:
    return db.query(Organization).filter(Organization.code == code.upper()).first()


def get_all(db: Session, skip: int = 0, limit: int = 200) -> list[Organization]:
    return db.query(Organization).offset(skip).limit(limit).all()


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
