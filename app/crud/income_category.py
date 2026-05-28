"""
CRUD untuk IncomeCategory dan seed data default.
"""
from sqlalchemy.orm import Session

from ..models.income_category import IncomeCategory, IncomeCalcMethod
from ..schemas.income_category import IncomeCategoryCreate, IncomeCategoryUpdate


def list_all(db: Session) -> list[IncomeCategory]:
    return db.query(IncomeCategory).order_by(IncomeCategory.sort_order, IncomeCategory.code).all()


def get(db: Session, category_id: int) -> IncomeCategory | None:
    return db.get(IncomeCategory, category_id)


def get_by_code(db: Session, code: str) -> IncomeCategory | None:
    return db.query(IncomeCategory).filter(IncomeCategory.code == code).first()


def create(db: Session, data: IncomeCategoryCreate) -> IncomeCategory:
    obj = IncomeCategory(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, cat: IncomeCategory, data: IncomeCategoryUpdate) -> IncomeCategory:
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(cat, k, v)
    db.commit()
    db.refresh(cat)
    return cat


def delete(db: Session, cat: IncomeCategory) -> None:
    db.delete(cat)
    db.commit()


def count(db: Session) -> int:
    return db.query(IncomeCategory).count()


def delete_all(db: Session) -> None:
    db.query(IncomeCategory).delete()
    db.commit()


def get_code_to_id_map(db: Session) -> dict[str, int]:
    """Return mapping {code: id} untuk semua IncomeCategory yang ada."""
    rows = db.query(IncomeCategory.code, IncomeCategory.id).all()
    return {row.code: row.id for row in rows}


_DEFAULT_INCOME_CATEGORIES: list[dict] = [
    # Simulated (UP/US/From Expense)
    {"code": "4110.01", "label": "Uang Pangkal (UP)", "calc_method": IncomeCalcMethod.SIMULATED_UP, "sort_order": 10},
    {"code": "4120.01", "label": "Uang Sekolah (US)", "calc_method": IncomeCalcMethod.SIMULATED_US, "sort_order": 20},
    {"code": "4120.02", "label": "Uang Komputer", "calc_method": IncomeCalcMethod.FROM_EXPENSE, "sort_order": 21},
    {"code": "4130.01", "label": "Pendapatan Ulangan Umum", "calc_method": IncomeCalcMethod.FROM_EXPENSE, "sort_order": 30},
    {"code": "4130.02", "label": "Pendapatan UAS/UAN", "calc_method": IncomeCalcMethod.FROM_EXPENSE, "sort_order": 31},
    {"code": "4140.01", "label": "Pendapatan PSB", "calc_method": IncomeCalcMethod.FROM_EXPENSE, "sort_order": 40},
    {"code": "4160.01", "label": "Kegiatan Siswa", "calc_method": IncomeCalcMethod.GRADE_BASED, "sort_order": 50},
    # Manual
    {"code": "4120.03", "label": "Uang Mandarin", "calc_method": IncomeCalcMethod.MANUAL, "sort_order": 22},
    {"code": "4120.04", "label": "Uang Perpustakaan", "calc_method": IncomeCalcMethod.MANUAL, "sort_order": 23},
    {"code": "4120.05", "label": "Denda Uang Sekolah", "calc_method": IncomeCalcMethod.MANUAL, "sort_order": 24},
    {"code": "4160.02", "label": "Kegiatan Lain", "calc_method": IncomeCalcMethod.MANUAL, "sort_order": 51},
    {"code": "4500.01", "label": "Pendapatan Non Operasional", "calc_method": IncomeCalcMethod.MANUAL, "sort_order": 60},
    {"code": "4510.01", "label": "Dana BOS", "calc_method": IncomeCalcMethod.SUM_FROM_BOS, "sort_order": 70},
    {"code": "4610.01", "label": "Sumbangan Pembangunan", "calc_method": IncomeCalcMethod.MANUAL, "sort_order": 80},
    {"code": "4620.01", "label": "Pendapatan Lain-lain", "calc_method": IncomeCalcMethod.MANUAL, "sort_order": 90},
    # Kontribusi diterima (CABANG / PUSAT)
    {"code": "4630.01", "label": "Kontribusi UP Diterima", "calc_method": IncomeCalcMethod.MANUAL, "sort_order": 100},
    {"code": "4630.02", "label": "Kontribusi US Diterima", "calc_method": IncomeCalcMethod.MANUAL, "sort_order": 101},
    {"code": "4630.05", "label": "Dana Pembangunan Diterima", "calc_method": IncomeCalcMethod.MANUAL, "sort_order": 102},
    {"code": "4630.06", "label": "Cadangan Karya Defisit Diterima", "calc_method": IncomeCalcMethod.MANUAL, "sort_order": 103},
    {"code": "4630.07", "label": "Subsidi dari PUSAT", "calc_method": IncomeCalcMethod.MANUAL, "sort_order": 104},
]


def seed_defaults(db: Session) -> int:
    """
    Semai kategori pendapatan standar jika tabel masih kosong.

    Returns:
        Jumlah baris yang disisipkan.
    """
    if count(db) > 0:
        return 0
    inserted = 0
    for item in _DEFAULT_INCOME_CATEGORIES:
        db.add(IncomeCategory(**item))
        inserted += 1
    db.commit()
    return inserted
