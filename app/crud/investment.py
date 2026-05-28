"""
CRUD untuk Investment (pembelian aset tetap baru).

Satu organisasi dapat memiliki banyak aset di berbagai kategori (1330.01–1330.08).
Depresiasi proporsional dihitung sebagai computed property di model Investment.
"""
from sqlalchemy.orm import Session

from ..models.investment import Investment
from ..schemas.investment import InvestmentCreate, InvestmentUpdate


def list_by_org(db: Session, org_id: int) -> list[Investment]:
    return db.query(Investment).filter(Investment.organization_id == org_id).all()


def get(db: Session, inv_id: int) -> Investment | None:
    return db.get(Investment, inv_id)


def create(db: Session, org_id: int, data: InvestmentCreate) -> Investment:
    obj = Investment(organization_id=org_id, **data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, inv: Investment, data: InvestmentUpdate) -> Investment:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(inv, key, value)
    db.commit()
    db.refresh(inv)
    return inv


def delete(db: Session, inv: Investment) -> None:
    db.delete(inv)
    db.commit()
