# Copilot Instructions — Budget Backend YPII

## Tujuan Proyek

Backend REST API untuk **simulasi Rencana Anggaran Belanja (RAB)** Yayasan Penyelenggaraan Ilahi Indonesia (YPII). Satu instance aplikasi = satu tahun anggaran (`BUDGET_YEAR`).

---

## Stack Teknologi

| Komponen | Library / Versi |
|----------|----------------|
| Web Framework | FastAPI ≥ 0.111 |
| ORM | SQLAlchemy 2.0+ (modern `Mapped`/`mapped_column`) |
| Validasi | Pydantic v2 (`model_config`, `@field_validator`) |
| Konfigurasi | pydantic-settings (baca dari `.env`) |
| Database | SQLite (satu file per instance/tahun) |
| Testing | pytest + httpx + `TestClient` |
| Linting | Ruff |

**Python minimum: 3.11+** (pakai sintaks `X | Y` untuk union type)

---

## Struktur Direktori

```
budget-backend-ypii/
├── app/
│   ├── main.py               # Entry point FastAPI, lifespan, CORS, router registration
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
│   └── test_simulation.py
├── .env.example
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

---

## Konsep Domain

### Hierarki Organisasi (`OrgType`)

| Tipe | Keterangan |
|------|-----------|
| `UNIT` | Satuan pendidikan (sekolah, daycare, TK, SD, SMP, SMA) |
| `CABANG` | Cabang YPII — mengelola beberapa UNIT |
| `PUSAT` | Kantor pusat YPII — rekapitulasi semua cabang |

### Sistem Kode Akun

| Prefix | Jenis |
|--------|-------|
| `4xxx` | Pendapatan |
| `5110–5250` | Biaya Operasional |
| `5500–5590` | Biaya Non Operasional (termasuk kontribusi) |
| `1330.xx` | Investasi Aset Tetap Baru |

Lihat `app/constants/account_codes.py` untuk daftar lengkap dan fungsi klasifikasi.

### Aturan Kalkulasi Utama

- **UP (Uang Pangkal):** Dari akun `5130.xx` + depresiasi investasi baru; tarif = total / `jml_siswa_baru`
- **US (Uang Sekolah):** Semua biaya operasional KECUALI UP-component dan direct-income accounts; tarif = total / (`total_siswa` × 12)
- **Direct income accounts:** Biaya tertentu (mis. `5160.16` → komputer, `5170.01` → kegiatan) langsung menjadi pendapatan akun 4xxx tertentu
- **Kontribusi default:** UP ke Pusat 4%, UP ke Cabang 12%, US ke Pusat 5%, US ke Cabang 10%
- **Depresiasi proporsional:** `dep_tahun_ini = (nilai_beli / umur_ekonomis) × (13 - bulan_mulai) / 12`

---

## Konvensi API

- Semua endpoint bertema organisasi berada di bawah `/organizations/{org_id}/`
- Simulasi: `GET /organizations/{org_id}/simulation/{type}` — `type` = `up | us | income | expenses | allocation | depreciation | summary`
- Kode organisasi dinormalisasi ke **uppercase** saat create/update
- Endpoint 404 jika organisasi tidak ditemukan; 422 jika validasi gagal; 409 jika kode duplikat

---

## Cara Menjalankan

```bash
# Salin dan sesuaikan konfigurasi
cp .env.example .env

# Install dependencies
pip install -r requirements.txt

# Jalankan server development
uvicorn app.main:app --reload

# Dokumentasi API otomatis tersedia di:
# http://localhost:8000/docs   (Swagger UI)
# http://localhost:8000/redoc  (ReDoc)
```

---

## Cara Menjalankan Test

> ⚠️ **WAJIB menggunakan Docker.** Dilarang menjalankan pytest langsung via `.venv` atau instalasi Python lokal.

```bash
# 1. Build image stage test
docker build --target test -t budget-backend-ypii:test .

# 2. Jalankan semua test di dalam container
docker run --rm budget-backend-ypii:test

# 3. Jalankan satu file test saja
docker run --rm budget-backend-ypii:test python -m pytest tests/test_simulation.py -v

# 4. Jalankan satu test case saja
docker run --rm budget-backend-ypii:test python -m pytest tests/test_simulation.py::TestUPSimulation::test_up_calculates_correctly -v
```

**Catatan penting untuk test fixtures (`tests/conftest.py`):**
- Engine SQLite in-memory session-scoped, terhubung via **`connection`-level binding** per test
- Setiap test mendapat koneksi + transaksi sendiri yang di-rollback setelah test selesai
- Ini memastikan tabel yang dibuat di `engine_fixture` tetap visible di `db_session`

---

## Variabel Konfigurasi (`.env`)

| Variabel | Default | Keterangan |
|----------|---------|-----------|
| `BUDGET_YEAR` | `2025-2026` | Tahun anggaran instance ini |
| `DATABASE_URL` | `sqlite:///./budget_ypii.db` | Path file SQLite |
| `APP_NAME` | `Budget YPII API` | Nama aplikasi |
| `DEBUG` | `false` | Mode debug |

---

## Panduan Pengembangan

### Menambah Model Baru
1. Buat file di `app/models/`
2. Import di `app/models/__init__.py` agar `Base.metadata.create_all()` mengenalinya
3. Buat schema di `app/schemas/`
4. Tambahkan CRUD di `app/crud/`
5. Buat router di `app/routers/` dan daftarkan di `app/main.py`

### Menambah Endpoint Simulasi Baru
- Tambahkan fungsi `simulate_xxx(db, org)` di `app/services/simulation.py`
- Tambahkan route baru di `app/routers/simulation.py`
- Tambahkan schema result di `app/schemas/simulation.py`

### Jangan Lakukan
- Jangan tambah logika bisnis di router atau CRUD — tempatkan di `services/simulation.py`
- Jangan hard-code kode akun di luar `app/constants/account_codes.py`
- Jangan modifikasi skema database tanpa migrasi (gunakan Alembic jika skala membesar)

---

## Wajib Dilakukan Saat Merevisi Kode

Setiap kali ada revisi kode, **semua langkah berikut wajib dilakukan secara bersamaan**:

### 1. Revisi Docstring
- Perbarui docstring fungsi/class/modul yang diubah agar mencerminkan perilaku terbaru
- Gunakan format Google-style docstring (Args, Returns, Raises)
- Jika fungsi baru ditambahkan, docstring wajib ada

### 2. Sesuaikan Unit Test
- Perbarui test yang sudah ada jika perilaku fungsi berubah
- Tambahkan test case baru untuk logika baru yang ditambahkan
- Pastikan semua test lulus menggunakan **Docker** (lihat bagian "Cara Menjalankan Test")
- **DILARANG** menjalankan test dengan `.venv/bin/pytest` atau `pytest` lokal secara langsung

### 3. Sesuaikan Copilot Instructions
- Perbarui file `.github/copilot-instructions.md` jika ada perubahan pada:
  - Konvensi API (endpoint baru, perubahan parameter, dll.)
  - Aturan kalkulasi domain
  - Struktur direktori
  - Kode akun yang digunakan

### 4. Pengujian di Docker

> ⚠️ **Semua pengujian — baik unit test (pytest) maupun verifikasi endpoint — WAJIB dijalankan via Docker.**
> Jangan pernah menggunakan `.venv`, `venv`, atau instalasi Python lokal untuk menjalankan test.

#### 4a. Unit Test (pytest)

```bash
# Build image stage test (menyertakan tests/ dan requirements-dev.txt)
docker build --target test -t budget-backend-ypii:test .

# Jalankan semua test
docker run --rm budget-backend-ypii:test
```

#### 4b. Verifikasi Endpoint API

```bash
# Build image production
docker build -t budget-backend-ypii:latest .

# Jalankan container di port non-standar
docker run -d --name budget-backend-test -p 8001:8000 budget-backend-ypii:latest

# Verifikasi endpoint berjalan normal
curl -s http://localhost:8001/docs -o /dev/null -w "Status: %{http_code}\n"

# Bersihkan container setelah selesai
docker stop budget-backend-test && docker rm budget-backend-test
```

---

## Konvensi Git Commit

Ketika diminta untuk melakukan commit:

1. **Gunakan bahasa Indonesia** untuk seluruh commit message
2. **Buat commit message seinformatif mungkin** — sertakan:
   - Baris pertama: ringkasan singkat perubahan (maks. 72 karakter)
   - Baris berikutnya (jika perlu): penjelasan *apa* yang berubah, *mengapa*, dan *dampaknya*
   - Sebutkan file atau modul yang terpengaruh jika relevan

Contoh:
```
Tambah endpoint simulasi kontribusi CABANG ke PUSAT

Implementasi simulate_allocation() di services/simulation.py.
Router baru di routers/simulation.py: GET /organizations/{id}/simulation/allocation.
Menghitung distribusi proporsional UP dan US berdasarkan jumlah siswa.
```

---

## Konvensi Tag (Semantic Versioning)

Ketika diminta untuk membuat tag, gunakan format **`vMAJOR.MINOR.PATCH`** berdasarkan jenis perubahan:

| Jenis Perubahan | Contoh | Bump |
|----------------|--------|------|
| Bug fix, perubahan kecil, perbaikan typo/doc | `v1.0.0` → `v1.0.1` | **Patch** |
| Fitur baru non-breaking: endpoint baru, model baru, skema baru | `v1.0.1` → `v1.1.0` | **Minor** |
| Perubahan breaking: ubah struktur DB, ubah kontrak API, hapus endpoint | `v1.1.0` → `v2.0.0` | **Major** |

Langkah membuat tag:
```bash
# Cek tag terakhir
git tag --sort=-v:refname | head -5

# Buat annotated tag
git tag -a v1.2.0 -m "Deskripsi singkat perubahan versi ini (bahasa Indonesia)"

# Push tag ke remote
git push origin v1.2.0
```

---

## Konvensi Push ke GitHub

Ketika diminta untuk push:

- **Ikuti instruksi eksplisit** dari user: push langsung ke `master` atau buat Pull Request (PR)
- Jika tidak ada instruksi eksplisit, **tanyakan** terlebih dahulu sebelum push

### Push langsung ke master
```bash
git push origin master
```

### Buat Pull Request
```bash
# Push ke branch baru terlebih dahulu
git push origin <nama-branch>

# Kemudian buat PR via GitHub CLI (jika tersedia)
gh pr create --title "Judul PR" --body "Deskripsi perubahan"
```
