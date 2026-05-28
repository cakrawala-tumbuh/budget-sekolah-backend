# Budget Backend

Backend REST API untuk **simulasi Rencana Anggaran Belanja (RAB)**.

Satu instance aplikasi merepresentasikan **satu tahun anggaran** (`BUDGET_YEAR`). API ini digunakan oleh frontend [Budget App](../budget-app-ypii) untuk menampilkan simulasi dan kalkulasi tarif UP/US.

---

## Stack Teknologi

| Komponen | Library / Versi |
|---|---|
| Web Framework | FastAPI ≥ 0.111 |
| ORM | SQLAlchemy 2.0+ (`Mapped` / `mapped_column`) |
| Validasi | Pydantic v2 |
| Konfigurasi | pydantic-settings (baca dari `.env`) |
| Autentikasi | JWT (`PyJWT`) + bcrypt |
| Database | SQLite |
| Testing | pytest + httpx |
| Linting | Ruff |

**Python minimum: 3.11+**

---

## Struktur Direktori

```
budget-backend/
├── app/
│   ├── main.py               # Entry point FastAPI, lifespan, CORS, router registration
│   ├── auth.py               # JWT authentication & dependency injection
│   ├── config.py             # Settings via pydantic-settings (baca .env)
│   ├── database.py           # Engine, SessionLocal, Base, get_db()
│   ├── constants/
│   │   └── account_codes.py  # Kode akun, klasifikasi, konstanta domain
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic v2 request/response schemas
│   ├── crud/                 # Fungsi database CRUD (tidak ada logika bisnis)
│   ├── services/
│   │   └── simulation.py     # Engine kalkulasi simulasi RAB
│   └── routers/              # FastAPI route handlers
├── tests/
│   ├── conftest.py           # Fixtures: engine, db_session, client
│   ├── test_organizations.py
│   ├── test_assumptions.py
│   ├── test_budget_entries.py
│   ├── test_investments.py
│   ├── test_parent_expense_allocations.py
│   └── test_simulation.py
├── .env.example              # Template konfigurasi environment
├── Dockerfile                # Multi-stage build (test + production)
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

---

## Cara Menjalankan (Development)

```bash
# 1. Salin dan sesuaikan konfigurasi
cp .env.example .env

# 2. Buat virtual environment dan install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Jalankan server development
uvicorn app.main:app --reload
```

Dokumentasi API otomatis tersedia di:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Cara Menjalankan via Docker

```bash
# Build image production
docker build -t budget-backend:latest .

# Jalankan container
docker run -d --name budget-backend -p 8000:8000 budget-backend:latest

# Verifikasi berjalan
curl http://localhost:8000/
```

---

## Cara Menjalankan Test

> ⚠️ **Wajib menggunakan Docker.** Jangan jalankan pytest langsung via `.venv` atau instalasi Python lokal.

```bash
# 1. Build image stage test
docker build --target test -t budget-backend:test .

# 2. Jalankan semua test
docker run --rm budget-backend:test

# 3. Jalankan satu file test
docker run --rm budget-backend:test python -m pytest tests/test_simulation.py -v

# 4. Jalankan satu test case
docker run --rm budget-backend:test python -m pytest tests/test_simulation.py::TestUPSimulation::test_up_calculates_correctly -v
```

---

## Variabel Konfigurasi (`.env`)

| Variabel | Default | Keterangan |
|---|---|---|
| `BUDGET_YEAR` | `2025-2026` | Tahun anggaran instance ini |
| `DATABASE_URL` | `sqlite:///./budget.db` | Path file SQLite |
| `APP_NAME` | `Budget Simulator` | Nama aplikasi |
| `DEBUG` | `false` | Mode debug |
| `ADMIN_PASSWORD` | `admin123` | Password akun admin (**wajib diganti di production**) |
| `JWT_SECRET_KEY` | `changeme-...` | Secret key JWT (**wajib diganti di production**) |
| `JWT_EXPIRE_MINUTES` | `480` | Masa berlaku token JWT (menit) |

---

## Endpoint Utama

### Health
| Method | Path | Keterangan |
|---|---|---|
| `GET` | `/` | Status aplikasi & tahun anggaran |
| `GET` | `/health` | Health check |

### Autentikasi
| Method | Path | Keterangan |
|---|---|---|
| `POST` | `/auth/login` | Login, mengembalikan JWT token |

### Organisasi
| Method | Path | Keterangan |
|---|---|---|
| `GET` | `/organizations` | Daftar semua organisasi |
| `POST` | `/organizations` | Buat organisasi baru |
| `GET` | `/organizations/{id}` | Detail organisasi |
| `PUT` | `/organizations/{id}` | Update organisasi |
| `DELETE` | `/organizations/{id}` | Hapus organisasi |

### Simulasi
| Method | Path | Keterangan |
|---|---|---|
| `GET` | `/organizations/{id}/simulation/up` | Simulasi komponen UP (UNIT only) |
| `GET` | `/organizations/{id}/simulation/us` | Simulasi komponen US (UNIT only) |
| `GET` | `/organizations/{id}/simulation/income` | Simulasi total pendapatan |
| `GET` | `/organizations/{id}/simulation/expenses` | Simulasi total biaya |
| `GET` | `/organizations/{id}/simulation/allocation` | Simulasi alokasi kontribusi |
| `GET` | `/organizations/{id}/simulation/depreciation` | Ringkasan depresiasi |
| `GET` | `/organizations/{id}/simulation/summary` | Ringkasan budget kas & akrual |

Dokumentasi lengkap dengan schema request/response tersedia di `/docs`.

---

## Konsep Domain

### Hierarki Organisasi (`OrgType`)

| Tipe | Keterangan |
|---|---|
| `UNIT` | Satuan pendidikan (sekolah, daycare, TK, SD, SMP, SMA) |
| `CABANG` | Cabang — mengelola beberapa UNIT |
| `PUSAT` | Kantor pusat — rekapitulasi semua cabang |

### Aturan Kalkulasi Utama

- **UP (Uang Pangkal):** komponen biaya `5130.xx` + depresiasi investasi baru; tarif = total / `jml_siswa_baru`
- **US (Uang Sekolah):** semua biaya operasional kecuali komponen UP dan direct-income accounts; tarif = total / (`total_siswa` × 12)
- **Kontribusi default:** UP ke Pusat 4%, UP ke Cabang 12%, US ke Pusat 5%, US ke Cabang 10%
- **Depresiasi proporsional:** `dep = (nilai_beli / umur_ekonomis) × (13 - bulan_mulai) / 12`

---

## Pengembangan

### Menambah Model Baru
1. Buat file di `app/models/`
2. Import di `app/models/__init__.py`
3. Buat schema di `app/schemas/`
4. Tambahkan CRUD di `app/crud/`
5. Buat router di `app/routers/` dan daftarkan di `app/main.py`

### Menambah Endpoint Simulasi Baru
1. Tambahkan fungsi `simulate_xxx(db, org)` di `app/services/simulation.py`
2. Tambahkan route baru di `app/routers/simulation.py`
3. Tambahkan schema result di `app/schemas/simulation.py`

### Konvensi Kode
- Logika bisnis hanya di `services/simulation.py` — jangan taruh di router atau CRUD
- Kode akun hanya di `app/constants/account_codes.py`
- Gunakan Google-style docstring untuk semua fungsi publik
- Linting: `ruff check app/`
