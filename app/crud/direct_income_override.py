"""CRUD untuk DirectIncomeOverride."""
from sqlalchemy.orm import Session

from ..models.direct_income_override import DirectIncomeOverride
from ..schemas.direct_income_override import DirectIncomeOverrideUpsert


def list_by_org(db: Session, org_id: int) -> list[DirectIncomeOverride]:
    return (
        db.query(DirectIncomeOverride)
        .filter(DirectIncomeOverride.organization_id == org_id)
        .all()
    )


def get_by_org_and_expense(
    db: Session, org_id: int, expense_category_id: int
) -> DirectIncomeOverride | None:
    return (
        db.query(DirectIncomeOverride)
        .filter(
            DirectIncomeOverride.organization_id == org_id,
            DirectIncomeOverride.expense_category_id == expense_category_id,
        )
        .first()
    )


def upsert(
    db: Session,
    org_id: int,
    expense_category_id: int,
    data: DirectIncomeOverrideUpsert,
) -> DirectIncomeOverride:
    """Buat atau update override. Jika sudah ada, nilai di-update."""
    obj = get_by_org_and_expense(db, org_id, expense_category_id)
    if obj is None:
        obj = DirectIncomeOverride(
            organization_id=org_id,
            expense_category_id=expense_category_id,
        )
        db.add(obj)
    obj.override_amount = data.override_amount
    obj.notes = data.notes
    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, obj: DirectIncomeOverride) -> None:
    db.delete(obj)
    db.commit()
