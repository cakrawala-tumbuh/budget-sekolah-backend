"""
CRUD untuk ExpenseCategory dan seed data default YPII.

seed_ypii_defaults() menyemai kategori biaya standar YPII jika tabel masih kosong.
Urutan seeding: IncomeCategory harus ada terlebih dahulu (untuk FK maps_to_income_category_id).
"""
from sqlalchemy.orm import Session

from ..models.expense_category import ExpenseCategory
from ..schemas.expense_category import ExpenseCategoryCreate, ExpenseCategoryUpdate


def list_all(db: Session) -> list[ExpenseCategory]:
    return db.query(ExpenseCategory).order_by(ExpenseCategory.sort_order, ExpenseCategory.code).all()


def get(db: Session, category_id: int) -> ExpenseCategory | None:
    return db.get(ExpenseCategory, category_id)


def get_by_code(db: Session, code: str) -> ExpenseCategory | None:
    return db.query(ExpenseCategory).filter(ExpenseCategory.code == code).first()


def create(db: Session, data: ExpenseCategoryCreate) -> ExpenseCategory:
    obj = ExpenseCategory(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, cat: ExpenseCategory, data: ExpenseCategoryUpdate) -> ExpenseCategory:
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(cat, k, v)
    db.commit()
    db.refresh(cat)
    return cat


def delete(db: Session, cat: ExpenseCategory) -> None:
    db.delete(cat)
    db.commit()


def count(db: Session) -> int:
    return db.query(ExpenseCategory).count()


def delete_all(db: Session) -> None:
    db.query(ExpenseCategory).delete()
    db.commit()


# ── Default YPII expense categories ──────────────────────────────────────────
# income_category_id akan di-resolve saat seed (berdasarkan code)

_YPII_EXPENSE_DEFAULTS: list[dict] = [
    # ── Operasional: Biaya Gaji (5110) ──
    {"code": "5110.01", "label": "Gaji", "is_operational": True, "is_up_component": False, "sort_order": 10},
    {"code": "5110.02", "label": "Honor", "is_operational": True, "is_up_component": False, "sort_order": 11},
    {"code": "5110.03", "label": "Pesangon", "is_operational": True, "is_up_component": False, "sort_order": 12},
    # ── Operasional: Tenaga Ahli (5120) ──
    {"code": "5120.01", "label": "Tenaga Ahli", "is_operational": True, "is_up_component": False, "sort_order": 20},
    # ── Operasional: Pengembangan Guru/Karyawan (5130) — UP component ──
    {"code": "5130.01", "label": "Pengabdian/Prestasi/Pensiun", "is_operational": True, "is_up_component": True, "sort_order": 30},
    {"code": "5130.02", "label": "Pembinaan Rohani", "is_operational": True, "is_up_component": True, "sort_order": 31},
    {"code": "5130.03", "label": "Pengembangan Profesi", "is_operational": True, "is_up_component": True, "sort_order": 32},
    {"code": "5130.04", "label": "Pengembangan Guru/Karyawan Lain", "is_operational": True, "is_up_component": False, "sort_order": 33},
    {"code": "5130.05", "label": "Studi Guru/Karyawan", "is_operational": True, "is_up_component": True, "sort_order": 34},
    {"code": "5130.06", "label": "Rekreasi", "is_operational": True, "is_up_component": True, "sort_order": 35},
    {"code": "5130.07", "label": "Seragam", "is_operational": True, "is_up_component": True, "sort_order": 36},
    {"code": "5130.08", "label": "Perayaan/Pesta", "is_operational": True, "is_up_component": True, "sort_order": 37},
    # ── Operasional: Ulangan (5140) — direct income ──
    {"code": "5140.01", "label": "Ulangan Umum", "is_operational": True, "is_up_component": False, "is_direct_income": True, "_maps_to_income_code": "4130.01", "sort_order": 40},
    {"code": "5140.02", "label": "UAS/UAN", "is_operational": True, "is_up_component": False, "is_direct_income": True, "_maps_to_income_code": "4130.02", "sort_order": 41},
    # ── Operasional: PSB (5150) — direct income ──
    {"code": "5150.01", "label": "Pendaftaran PSB", "is_operational": True, "is_up_component": False, "is_direct_income": True, "_maps_to_income_code": "4140.01", "sort_order": 50},
    # ── Operasional: Biaya Operasional Sekolah (5160) ──
    {"code": "5160.01", "label": "Perpustakaan", "is_operational": True, "is_up_component": False, "sort_order": 60},
    {"code": "5160.02", "label": "Makan/Minum", "is_operational": True, "is_up_component": False, "sort_order": 61},
    {"code": "5160.03", "label": "Buku Pelajaran", "is_operational": True, "is_up_component": False, "sort_order": 62},
    {"code": "5160.04", "label": "UKS", "is_operational": True, "is_up_component": False, "sort_order": 63},
    {"code": "5160.05", "label": "LKS/Lembar Kerja", "is_operational": True, "is_up_component": False, "sort_order": 64},
    {"code": "5160.06", "label": "Lomba/Olimpiade", "is_operational": True, "is_up_component": False, "sort_order": 65},
    {"code": "5160.07", "label": "Laboratorium", "is_operational": True, "is_up_component": False, "sort_order": 66},
    {"code": "5160.16", "label": "Biaya Komputer", "is_operational": True, "is_up_component": False, "is_direct_income": True, "_maps_to_income_code": "4120.02", "sort_order": 76},
    # ── Operasional: Kegiatan Siswa (5170) — GRADE_BASED direct income ──
    {"code": "5170.01", "label": "Kegiatan Siswa", "is_operational": True, "is_up_component": False, "is_direct_income": True, "_maps_to_income_code": "4160.01", "sort_order": 80},
    {"code": "5170.02", "label": "Kegiatan Lain", "is_operational": True, "is_up_component": False, "sort_order": 81},
    # ── Operasional: Biaya Khusus (5180) ──
    {"code": "5180.01", "label": "Biaya Khusus", "is_operational": True, "is_up_component": False, "sort_order": 90},
    # ── Operasional: Admin & Umum (5190) ──
    {"code": "5190.01", "label": "Administrasi dan Umum", "is_operational": True, "is_up_component": False, "sort_order": 100},
    # ── Operasional: Utilities (5200) ──
    {"code": "5200.01", "label": "Listrik", "is_operational": True, "is_up_component": False, "sort_order": 110},
    {"code": "5200.02", "label": "Air", "is_operational": True, "is_up_component": False, "sort_order": 111},
    {"code": "5200.03", "label": "Telepon/Internet", "is_operational": True, "is_up_component": False, "sort_order": 112},
    # ── Operasional: Transportasi, Asuransi, Sewa, Pajak, Pemeliharaan ──
    {"code": "5210.01", "label": "Transportasi", "is_operational": True, "is_up_component": False, "sort_order": 120},
    {"code": "5220.01", "label": "Asuransi", "is_operational": True, "is_up_component": False, "sort_order": 130},
    {"code": "5230.01", "label": "Sewa", "is_operational": True, "is_up_component": False, "sort_order": 140},
    {"code": "5240.01", "label": "Pajak", "is_operational": True, "is_up_component": False, "sort_order": 150},
    {"code": "5250.01", "label": "Pemeliharaan Aktiva Tetap", "is_operational": True, "is_up_component": False, "sort_order": 160},
    # ── Non-Operasional: Kantin, Riso, Lain ──
    {"code": "5510.01", "label": "Biaya Kantin", "is_operational": False, "is_up_component": False, "sort_order": 200},
    {"code": "5520.01", "label": "Biaya Riso/Koperasi", "is_operational": False, "is_up_component": False, "sort_order": 210},
    {"code": "5530.01", "label": "Biaya Non Operasional Lain", "is_operational": False, "is_up_component": False, "sort_order": 220},
    # ── Non-Operasional: Kontribusi (5590) ──
    {"code": "5590.01", "label": "Kontribusi UP ke Pusat", "is_operational": False, "contribution_role": "up_to_pusat", "sort_order": 300},
    {"code": "5590.02", "label": "Kontribusi US ke Pusat", "is_operational": False, "contribution_role": "us_to_pusat", "sort_order": 301},
    {"code": "5590.03", "label": "Kontribusi UP ke Cabang", "is_operational": False, "contribution_role": "up_to_cabang", "sort_order": 302},
    {"code": "5590.04", "label": "Kontribusi US ke Cabang", "is_operational": False, "contribution_role": "us_to_cabang", "sort_order": 303},
    {"code": "5590.05", "label": "Dana Pembangunan", "is_operational": False, "contribution_role": "development_fund", "sort_order": 304},
    {"code": "5590.06", "label": "Cadangan Karya Defisit", "is_operational": False, "contribution_role": "deficit_reserve", "sort_order": 305},
    {"code": "5590.07", "label": "Subsidi ke Unit (PUSAT)", "is_operational": False, "contribution_role": "subsidy_to_unit", "sort_order": 306},
    {"code": "5590.08", "label": "Sewa Tanah", "is_operational": False, "contribution_role": "land_lease", "sort_order": 307},
    {"code": "5590.09", "label": "Saldo Operasional", "is_operational": False, "contribution_role": "operating_balance", "sort_order": 308},
]


def seed_ypii_defaults(db: Session, income_code_to_id: dict[str, int]) -> int:
    """
    Semai kategori biaya standar YPII jika tabel masih kosong.

    Args:
        db: Database session.
        income_code_to_id: Mapping kode IncomeCategory → id (dari seeding IncomeCategory).

    Returns:
        Jumlah baris yang disisipkan.
    """
    if count(db) > 0:
        return 0
    inserted = 0
    for item in _YPII_EXPENSE_DEFAULTS:
        data = {k: v for k, v in item.items() if not k.startswith("_")}
        # Resolve FK ke IncomeCategory
        maps_code = item.get("_maps_to_income_code")
        if maps_code:
            data["maps_to_income_category_id"] = income_code_to_id.get(maps_code)
        obj = ExpenseCategory(**data)
        db.add(obj)
        inserted += 1
    db.commit()
    return inserted
