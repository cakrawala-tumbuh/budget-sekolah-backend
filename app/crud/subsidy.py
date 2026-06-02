"""
CRUD untuk Subsidy — subsidi langsung dari Cabang/Pusat ke unit penerima.
"""
from sqlalchemy.orm import Session

from ..models.subsidy import Subsidy
from ..schemas.subsidy import SubsidyCreate, SubsidyUpdate


def list_by_provider(db: Session, provider_org_id: int) -> list[Subsidy]:
    """Semua subsidi yang diberikan oleh organisasi pemberi tertentu."""
    return (
        db.query(Subsidy)
        .filter(Subsidy.provider_org_id == provider_org_id)
        .order_by(Subsidy.id)
        .all()
    )


def list_active_by_provider(db: Session, provider_org_id: int) -> list[Subsidy]:
    return (
        db.query(Subsidy)
        .filter(
            Subsidy.provider_org_id == provider_org_id,
            Subsidy.is_active == True,  # noqa: E712
        )
        .order_by(Subsidy.id)
        .all()
    )


def list_active_by_recipient(db: Session, recipient_org_id: int) -> list[Subsidy]:
    """Semua subsidi aktif yang diterima oleh organisasi penerima tertentu."""
    return (
        db.query(Subsidy)
        .filter(
            Subsidy.recipient_org_id == recipient_org_id,
            Subsidy.is_active == True,  # noqa: E712
        )
        .order_by(Subsidy.id)
        .all()
    )


def get(db: Session, subsidy_id: int) -> Subsidy | None:
    return db.get(Subsidy, subsidy_id)


def create(db: Session, provider_org_id: int, data: SubsidyCreate) -> Subsidy:
    obj = Subsidy(provider_org_id=provider_org_id, **data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, subsidy: Subsidy, data: SubsidyUpdate) -> Subsidy:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(subsidy, key, value)
    db.commit()
    db.refresh(subsidy)
    return subsidy


def delete(db: Session, subsidy: Subsidy) -> None:
    db.delete(subsidy)
    db.commit()
