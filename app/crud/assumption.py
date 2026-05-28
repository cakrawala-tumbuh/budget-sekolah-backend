"""
CRUD untuk UnitAssumption.

Menggunakan pola upsert: jika baris sudah ada untuk org_id maka diperbarui,
jika belum ada maka dibuat baru. Hanya satu baris asumsi per organisasi.
"""
from sqlalchemy.orm import Session

from ..models.assumption import UnitAssumption
from ..schemas.assumption import UnitAssumptionCreate, UnitAssumptionUpdate


def get(db: Session, org_id: int) -> UnitAssumption | None:
    return db.query(UnitAssumption).filter(UnitAssumption.organization_id == org_id).first()


def upsert(db: Session, org_id: int, data: UnitAssumptionCreate | UnitAssumptionUpdate) -> UnitAssumption:
    obj = get(db, org_id)
    if obj is None:
        obj = UnitAssumption(organization_id=org_id, **data.model_dump())
        db.add(obj)
    else:
        for key, value in data.model_dump().items():
            setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, org_id: int) -> bool:
    obj = get(db, org_id)
    if obj is None:
        return False
    db.delete(obj)
    db.commit()
    return True
