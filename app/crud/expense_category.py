"""
CRUD untuk ExpenseCategory dan seed data default.

seed_defaults() menyemai kategori biaya standar jika tabel masih kosong.
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


# ── Default expense categories ───────────────────────────────────────────────
# income_category_id akan di-resolve saat seed (berdasarkan code)

_DEFAULT_EXPENSE_CATEGORIES: list[dict] = [
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
    {"code": "5130.09", "label": "Kesehatan", "is_operational": True, "is_up_component": False, "sort_order": 38},
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
    {"code": "5160.08", "label": "Pertemuan Guru Internal & Eksternal", "is_operational": True, "is_up_component": False, "sort_order": 67},
    {"code": "5160.09", "label": "Rapat Rutin Intern Sekolah", "is_operational": True, "is_up_component": False, "sort_order": 68},
    {"code": "5160.10", "label": "Raker Kantor", "is_operational": True, "is_up_component": False, "sort_order": 69},
    {"code": "5160.11", "label": "Perayaan/Pesta Sekolah", "is_operational": True, "is_up_component": False, "sort_order": 70},
    {"code": "5160.12", "label": "P3K Sekolah", "is_operational": True, "is_up_component": False, "sort_order": 71},
    {"code": "5160.13", "label": "Keperluan Sekolah", "is_operational": True, "is_up_component": False, "sort_order": 72},
    {"code": "5160.14", "label": "Alat-alat Olah Raga", "is_operational": True, "is_up_component": False, "sort_order": 73},
    {"code": "5160.15", "label": "Promosi Sekolah", "is_operational": True, "is_up_component": False, "sort_order": 74},
    {"code": "5160.16", "label": "Biaya Komputer", "is_operational": True, "is_up_component": False, "is_direct_income": True, "_maps_to_income_code": "4120.02", "sort_order": 76},
    {"code": "5160.17", "label": "Wisuda/Pelepasan", "is_operational": True, "is_up_component": False, "sort_order": 77},
    {"code": "5160.18", "label": "Biaya BOS", "is_operational": True, "is_up_component": False, "sort_order": 78},
    {"code": "5160.19", "label": "Biaya BOP", "is_operational": True, "is_up_component": False, "sort_order": 79},
    {"code": "5160.20", "label": "Biaya PBOS", "is_operational": True, "is_up_component": False, "sort_order": 85},
    {"code": "5160.21", "label": "Biaya Day Care/Student Care", "is_operational": True, "is_up_component": False, "sort_order": 86},
    # ── Operasional: Kegiatan Siswa (5170) — GRADE_BASED direct income ──
    {"code": "5170.01", "label": "Kegiatan Siswa", "is_operational": True, "is_up_component": False, "is_direct_income": True, "_maps_to_income_code": "4160.01", "sort_order": 80},
    {"code": "5170.02", "label": "Kegiatan Lain", "is_operational": True, "is_up_component": False, "sort_order": 81},
    # ── Operasional: Biaya Khusus (5180) ──
    {"code": "5180.01", "label": "Biaya Khusus", "is_operational": True, "is_up_component": False, "sort_order": 90},
    # ── Operasional: Admin & Umum (5190) ──
    {"code": "5190.01", "label": "Administrasi dan Umum", "is_operational": True, "is_up_component": False, "sort_order": 100},
    {"code": "5190.02", "label": "Administrasi Khusus", "is_operational": True, "is_up_component": False, "sort_order": 101},
    {"code": "5190.03", "label": "Ongkos Kirim", "is_operational": True, "is_up_component": False, "sort_order": 102},
    {"code": "5190.04", "label": "Surat Kabar dan Majalah", "is_operational": True, "is_up_component": False, "sort_order": 103},
    {"code": "5190.05", "label": "Konsumsi", "is_operational": True, "is_up_component": False, "sort_order": 104},
    {"code": "5190.06", "label": "Keamanan", "is_operational": True, "is_up_component": False, "sort_order": 105},
    {"code": "5190.07", "label": "Keperluan Rumah Tangga", "is_operational": True, "is_up_component": False, "sort_order": 106},
    {"code": "5190.08", "label": "Administrasi Bank", "is_operational": True, "is_up_component": False, "sort_order": 107},
    {"code": "5190.09", "label": "Biaya Umum Lain", "is_operational": True, "is_up_component": False, "sort_order": 108},
    # ── Operasional: Utilities (5200) ──
    {"code": "5200.01", "label": "Listrik", "is_operational": True, "is_up_component": False, "sort_order": 110},
    {"code": "5200.02", "label": "Air", "is_operational": True, "is_up_component": False, "sort_order": 111},
    {"code": "5200.03", "label": "Telepon/Internet", "is_operational": True, "is_up_component": False, "sort_order": 112},
    {"code": "5200.04", "label": "Internet", "is_operational": True, "is_up_component": False, "sort_order": 113},
    {"code": "5200.05", "label": "Telekomunikasi", "is_operational": True, "is_up_component": False, "sort_order": 114},
    # ── Operasional: Transportasi, Asuransi, Sewa, Pajak, Pemeliharaan ──
    {"code": "5210.01", "label": "Transportasi", "is_operational": True, "is_up_component": False, "sort_order": 120},
    {"code": "5210.02", "label": "Perjalanan Dinas", "is_operational": True, "is_up_component": False, "sort_order": 121},
    {"code": "5220.01", "label": "Asuransi", "is_operational": True, "is_up_component": False, "sort_order": 130},
    {"code": "5220.02", "label": "Asuransi Kendaraan", "is_operational": True, "is_up_component": False, "sort_order": 131},
    {"code": "5220.03", "label": "Asuransi Komputer", "is_operational": True, "is_up_component": False, "sort_order": 132},
    {"code": "5220.04", "label": "Asuransi Jiwa", "is_operational": True, "is_up_component": False, "sort_order": 133},
    {"code": "5230.01", "label": "Sewa", "is_operational": True, "is_up_component": False, "sort_order": 140},
    {"code": "5240.01", "label": "Pajak", "is_operational": True, "is_up_component": False, "sort_order": 150},
    {"code": "5240.02", "label": "Pajak Bumi Bangunan (PBB)", "is_operational": True, "is_up_component": False, "sort_order": 151},
    {"code": "5240.03", "label": "Pajak Sewa (PPh 23)", "is_operational": True, "is_up_component": False, "sort_order": 152},
    {"code": "5240.04", "label": "BPHTB", "is_operational": True, "is_up_component": False, "sort_order": 153},
    {"code": "5240.05", "label": "PPh Ps 4 (PPh Kontraktor)", "is_operational": True, "is_up_component": False, "sort_order": 154},
    {"code": "5240.06", "label": "Pajak Kegiatan Membangun Sendiri (KMS)", "is_operational": True, "is_up_component": False, "sort_order": 155},
    {"code": "5240.07", "label": "Denda PPh Badan", "is_operational": True, "is_up_component": False, "sort_order": 156},
    {"code": "5240.08", "label": "Denda PPh Lain", "is_operational": True, "is_up_component": False, "sort_order": 157},
    {"code": "5250.01", "label": "Pemeliharaan Aktiva Tetap", "is_operational": True, "is_up_component": False, "sort_order": 160},
    {"code": "5250.02", "label": "Pemeliharaan Peralatan dan Instalasi Listrik", "is_operational": True, "is_up_component": False, "sort_order": 161},
    {"code": "5250.03", "label": "Pemeliharaan Inventaris Kendaraan", "is_operational": True, "is_up_component": False, "sort_order": 162},
    {"code": "5250.04", "label": "Pemeliharaan Inventaris Kantor", "is_operational": True, "is_up_component": False, "sort_order": 163},
    {"code": "5250.05", "label": "Pemeliharaan Inventaris Meubelair", "is_operational": True, "is_up_component": False, "sort_order": 164},
    {"code": "5250.06", "label": "Pemeliharaan Inventaris Lain", "is_operational": True, "is_up_component": False, "sort_order": 165},
    {"code": "5250.07", "label": "Pemeliharaan Inventaris Alat Musik & Drum Band", "is_operational": True, "is_up_component": False, "sort_order": 166},
    {"code": "5250.08", "label": "Pemeliharaan Inventaris Lab MIPA/Bahasa", "is_operational": True, "is_up_component": False, "sort_order": 167},
    {"code": "5250.09", "label": "Pemeliharaan Inventaris Lab Komputer", "is_operational": True, "is_up_component": False, "sort_order": 168},
    {"code": "5250.10", "label": "Pemeliharaan Peralatan Perpustakaan", "is_operational": True, "is_up_component": False, "sort_order": 169},
    {"code": "5250.11", "label": "Pemeliharaan Alat-alat Olah Raga", "is_operational": True, "is_up_component": False, "sort_order": 170},
    # ── Non-Operasional: Kantin, Riso, Lain ──
    {"code": "5510.01", "label": "Biaya Kantin", "is_operational": False, "is_up_component": False, "sort_order": 200},
    {"code": "5520.01", "label": "Biaya Riso/Koperasi", "is_operational": False, "is_up_component": False, "sort_order": 210},
    {"code": "5520.02", "label": "Biaya Koperasi", "is_operational": False, "is_up_component": False, "sort_order": 211},
    {"code": "5530.01", "label": "Biaya Non Operasional Lain", "is_operational": False, "is_up_component": False, "sort_order": 220},
    {"code": "5530.02", "label": "Biaya Lain-lain", "is_operational": False, "is_up_component": False, "sort_order": 221},
    {"code": "5540.01", "label": "Biaya Investasi", "is_operational": False, "is_up_component": False, "sort_order": 225},
    # ── Non-Operasional: Pajak penghasilan pasif ──
    {"code": "5550.01", "label": "PPh Bunga Tabungan Bank", "is_operational": False, "is_up_component": False, "sort_order": 230},
    {"code": "5550.02", "label": "PPh Bunga Deposito Bank", "is_operational": False, "is_up_component": False, "sort_order": 231},
    {"code": "5560.01", "label": "PPh Bunga Tabungan Koperasi", "is_operational": False, "is_up_component": False, "sort_order": 235},
    {"code": "5560.02", "label": "PPh Bunga Deposito Koperasi", "is_operational": False, "is_up_component": False, "sort_order": 236},
    {"code": "5570.01", "label": "PPh Investasi", "is_operational": False, "is_up_component": False, "sort_order": 240},
    # ── Non-Operasional: Sumbangan & Beasiswa ──
    {"code": "5580.01", "label": "Sumbangan Intern", "is_operational": False, "is_up_component": False, "sort_order": 245},
    {"code": "5580.02", "label": "Sumbangan Ekstern", "is_operational": False, "is_up_component": False, "sort_order": 246},
    {"code": "5580.03", "label": "Sumbangan ke Diknas", "is_operational": False, "is_up_component": False, "sort_order": 247},
    {"code": "5580.04", "label": "Sumbangan antar Yayasan Katolik", "is_operational": False, "is_up_component": False, "sort_order": 248},
    {"code": "5580.05", "label": "Beasiswa Intern", "is_operational": False, "is_up_component": False, "sort_order": 249},
    {"code": "5580.06", "label": "Beasiswa Ekstern", "is_operational": False, "is_up_component": False, "sort_order": 250},
    {"code": "5580.07", "label": "Kepedulian Sosial", "is_operational": False, "is_up_component": False, "sort_order": 251},
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


def seed_defaults(db: Session, income_code_to_id: dict[str, int]) -> int:
    """
    Semai kategori biaya standar. Bersifat additive — hanya menyisipkan kode
    yang belum ada, tidak menghapus atau mengubah data yang sudah ada.

    Args:
        db: Database session.
        income_code_to_id: Mapping kode IncomeCategory → id (dari seeding IncomeCategory).

    Returns:
        Jumlah baris yang disisipkan.
    """
    existing_codes = {cat.code for cat in list_all(db)}
    inserted = 0
    for item in _DEFAULT_EXPENSE_CATEGORIES:
        if item["code"] in existing_codes:
            continue
        data = {k: v for k, v in item.items() if not k.startswith("_")}
        # Resolve FK ke IncomeCategory
        maps_code = item.get("_maps_to_income_code")
        if maps_code:
            data["maps_to_income_category_id"] = income_code_to_id.get(maps_code)
        obj = ExpenseCategory(**data)
        db.add(obj)
        inserted += 1
    if inserted:
        db.commit()
    return inserted
