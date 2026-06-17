"""CRUD untuk FinancialInvestment (instrumen investasi keuangan CABANG/PUSAT)."""
from sqlalchemy.orm import Session

from ..models.financial_investment import FinancialInvestment
from ..schemas.financial_investment import FinancialInvestmentCreate, FinancialInvestmentUpdate


def list_by_org(db: Session, org_id: int) -> list[FinancialInvestment]:
    return db.query(FinancialInvestment).filter(
        FinancialInvestment.organization_id == org_id
    ).all()


def get(db: Session, inv_id: int) -> FinancialInvestment | None:
    return db.get(FinancialInvestment, inv_id)


def create(db: Session, org_id: int, data: FinancialInvestmentCreate) -> FinancialInvestment:
    obj = FinancialInvestment(organization_id=org_id, **data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(
    db: Session, inv: FinancialInvestment, data: FinancialInvestmentUpdate
) -> FinancialInvestment:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(inv, key, value)
    db.commit()
    db.refresh(inv)
    return inv


def delete(db: Session, inv: FinancialInvestment) -> None:
    db.delete(inv)
    db.commit()
