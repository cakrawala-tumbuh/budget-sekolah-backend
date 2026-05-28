"""
CRUD untuk InvestmentCategory dan seed data default.
"""
from sqlalchemy.orm import Session

from ..models.investment_category import InvestmentCategory
from ..schemas.investment_category import InvestmentCategoryCreate, InvestmentCategoryUpdate


def list_all(db: Session) -> list[InvestmentCategory]:
    return db.query(InvestmentCategory).order_by(InvestmentCategory.sort_order, InvestmentCategory.code).all()


def get(db: Session, category_id: int) -> InvestmentCategory | None:
    return db.get(InvestmentCategory, category_id)


def get_by_code(db: Session, code: str) -> InvestmentCategory | None:
    return db.query(InvestmentCategory).filter(InvestmentCategory.code == code).first()


def create(db: Session, data: InvestmentCategoryCreate) -> InvestmentCategory:
    obj = InvestmentCategory(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, cat: InvestmentCategory, data: InvestmentCategoryUpdate) -> InvestmentCategory:
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(cat, k, v)
    db.commit()
    db.refresh(cat)
    return cat


def delete(db: Session, cat: InvestmentCategory) -> None:
    db.delete(cat)
    db.commit()


def count(db: Session) -> int:
    return db.query(InvestmentCategory).count()


def delete_all(db: Session) -> None:
    db.query(InvestmentCategory).delete()
    db.commit()


_DEFAULT_INVESTMENT_CATEGORIES: list[dict] = [
    {"code": "1330.01", "label": "Inventaris Kendaraan", "default_economic_life": 5, "sort_order": 1},
    {"code": "1330.02", "label": "Inventaris Kantor", "default_economic_life": 4, "sort_order": 2},
    {"code": "1330.03", "label": "Inventaris Meubelair", "default_economic_life": 8, "sort_order": 3},
    {"code": "1330.04", "label": "Inventaris Lain-lain", "default_economic_life": 4, "sort_order": 4},
    {"code": "1330.05", "label": "Inventaris Alat Musik", "default_economic_life": 5, "sort_order": 5},
    {"code": "1330.06", "label": "Inventaris Lab MIPA/Bahasa", "default_economic_life": 5, "sort_order": 6},
    {"code": "1330.07", "label": "Inventaris Lab Komputer", "default_economic_life": 4, "sort_order": 7},
    {"code": "1330.08", "label": "Inventaris Perpustakaan", "default_economic_life": 5, "sort_order": 8},
]


def seed_defaults(db: Session) -> int:
    """
    Semai kategori investasi standar jika tabel masih kosong.

    Returns:
        Jumlah baris yang disisipkan.
    """
    if count(db) > 0:
        return 0
    inserted = 0
    for item in _DEFAULT_INVESTMENT_CATEGORIES:
        db.add(InvestmentCategory(**item))
        inserted += 1
    db.commit()
    return inserted
