# Changelog

Semua perubahan penting pada proyek ini didokumentasikan di berkas ini.

Format mengacu pada [Keep a Changelog](https://keepachangelog.com/id/1.1.0/),
dan proyek ini menganut [Semantic Versioning](https://semver.org/lang/id/).

## [Unreleased]

### Ditambahkan
- Field `total_physical_investments` dan `total_financial_investments` pada
  response `BudgetSummary` (`GET /organizations/{org_id}/simulation/summary`),
  memecah `total_investments` — yang selama ini menggabungkan pembelian aset
  tetap (`Investment.purchase_price`) dan investasi keuangan CABANG/PUSAT
  (`FinancialInvestment.amount`) — menjadi dua komponen terpisah. Field
  `total_investments` dipertahankan sebagai gabungan untuk backward
  compatibility; rumus `cash_surplus_deficit`/`cash_surplus_deficit_auto`
  tidak berubah.

## [1.34.1] - 2026-07-03

### Diperbaiki
- `simulate_income` untuk organisasi CABANG/PUSAT: pendapatan setoran UP/US
  (`4630.01`/`4630.02`) dari child UNIT kini ikut di-gate oleh parameter
  `include_parent_allocation`. Sebelumnya blok ini selalu dijalankan meski
  `include_parent_allocation=false`, sehingga endpoint `summary-comparative`
  menampilkan baris Cabang/Pusat yang identik pada tab "Dengan Alokasi ke
  Induk" maupun "Tanpa Alokasi ke Induk" — melanggar simetri konsolidasi
  1:1 dengan beban alokasi di sisi unit (`simulate_expenses`).

## [1.34.0] - 2026-07-03

### Ditambahkan
- Endpoint baru `GET /organizations/{org_id}/simulation/summary-comparative`
  (khusus CABANG/PUSAT, 422 untuk UNIT) yang mengembalikan ringkasan RAB
  organisasi itu sendiri beserta seluruh UNIT di bawahnya (untuk PUSAT
  mencakup unit lintas semua cabang). Setiap baris menyertakan dua varian
  `BudgetSummary`: `summary_with_allocation` dan `summary_without_allocation`,
  memakai fungsi `simulate_summary` dan `simulate_up`/`simulate_us` yang sudah
  ada (mode override vs otomatis sudah tersedia sebagai pasangan field di
  `BudgetSummary`, tidak perlu parameter baru).

## [1.33.0] - 2026-07-03

### Ditambahkan
- Parameter query `include_parent_allocation` (default `true`) pada endpoint
  simulasi `up`, `us`, `expenses`, `income`, dan `summary`. Saat diset
  `false`, simulasi UNIT mengabaikan seluruh beban yang dialokasikan dari
  Cabang/Pusat (komponen biaya, depresiasi investasi baru & aset lama,
  investasi keuangan), sehingga menghasilkan tarif UP/US dan total biaya
  yang murni berasal dari data unit itu sendiri. Perilaku default (tanpa
  parameter) tidak berubah.

## [1.32.0] - 2026-06-17

### Ditambahkan
- **Investasi Keuangan CABANG/PUSAT**: Model `FinancialInvestment` dan tabel
  `financial_investments` untuk mencatat instrumen investasi keuangan (saham,
  reksa dana, obligasi, deposito, dll.) milik CABANG atau PUSAT.
- Endpoint CRUD baru `GET/POST/PUT/DELETE /organizations/{org_id}/financial-investments`.
  Operasi write divalidasi hanya untuk CABANG dan PUSAT — UNIT tidak dapat
  mengelola investasi keuangan.
- Total investasi keuangan CABANG/PUSAT dialokasikan ke UNIT anak secara
  proporsional berdasarkan `new_students` (pct_up), muncul sebagai beban UP di
  simulasi unit penerima.
- Alokasi investasi keuangan dari Cabang dan Pusat ditambahkan ke
  `UPSimulation` sebagai field `cabang_financial_investment_allocated` dan
  `pusat_financial_investment_allocated`, serta masuk `total_up_cost_with_dep`.
- Alokasi investasi keuangan muncul di `ExpenseSimulation` unit penerima
  sebagai baris operasional `[Alokasi Cabang/Pusat] Investasi Keuangan`.
- Total investasi keuangan org itu sendiri masuk `total_investments` di
  `BudgetSummary` (cash outflow), konsisten dengan pembelian aset tetap.
- Setoran UP unit ke induk (`_unit_setoran_to_ancestor`) sudah menyertakan
  porsi investasi keuangan induk agar konsolidasi unit–induk tetap seimbang.

## [1.31.0] - 2026-06-11

### Ditambahkan
- Endpoint `POST /auth/logout` untuk invalidasi token saat ini di sisi server.
  Logout menaikkan `token_version` user sehingga semua token lama yang pernah
  diterbitkan langsung ditolak — sesi tidak dapat direuse meski token belum
  kedaluwarsa.
- Kolom `token_version` (integer, default 0) pada tabel `users`; migrasi ringan
  otomatis dijalankan saat startup untuk database lama.
- Field `ver` (token version) disertakan dalam payload JWT sejak login agar
  `get_current_user` dapat memvalidasi kecocokannya dengan nilai di database.

## [1.22.1] - 2026-06-11

### Diperbaiki
- Algoritma proporsi per unit (Siswa Baru UP & Total Siswa US) kini menjamin
  total seluruh persentase final tepat **100%** meski sebagian unit menggunakan
  override manual. Unit tanpa override mendapat bagian dari sisa
  (1 − total_semua_override) dibagi proporsional berdasarkan jumlah siswa,
  bukan dibagi terhadap total siswa seluruh unit. Sebelumnya total proporsi bisa
  melebihi 100% bila ada campuran override dan auto.

## [1.22.0] - 2026-06-10

### Ditambahkan
- Endpoint `PATCH /organizations/{id}/budget-entries/bulk-move-category` untuk
  memindahkan banyak entri biaya ke kategori lain sekaligus dalam satu request.
  Menerima `entry_ids` (daftar ID) dan `expense_category_id` tujuan; hanya
  mengubah entri milik organisasi yang bersangkutan.

## [1.21.1] - 2026-06-10

### Diperbaiki
- `BudgetEntryUpdate` kini menyertakan field `expense_category_id` sehingga
  pengguna dapat mengubah kategori biaya (operasional maupun non-operasional)
  pada entri yang sudah ada. Sebelumnya field ini tidak ada di schema update
  sehingga perubahan kategori dari UI tidak disimpan ke database.

## [1.21.0] - 2026-06-08

### Ditambahkan
- Model `DirectIncomeOverride` (`app/models/direct_income_override.py`): tabel
  `direct_income_overrides` menyimpan override nilai direct income per organisasi
  per expense category, dengan unique constraint `(organization_id, expense_category_id)`.
- CRUD `app/crud/direct_income_override.py`: fungsi `list_by_org`, `get_by_org_and_expense`,
  `upsert`, dan `delete`.
- Schema `DirectIncomeOverrideUpsert` dan `DirectIncomeOverrideRead`
  di `app/schemas/direct_income_override.py`.
- Router `app/routers/direct_income_overrides.py` dengan tiga endpoint:
  `GET /organizations/{org_id}/direct-income-overrides`,
  `PUT /organizations/{org_id}/direct-income-overrides/{expense_category_id}` (upsert),
  `DELETE /organizations/{org_id}/direct-income-overrides/{expense_category_id}` (reset ke otomatis).

### Diubah
- `simulate_direct_income()` dan `simulate_income()` di `app/services/simulation.py`:
  memeriksa tabel override sebelum menggunakan nilai otomatis dari budget entry.
  Bila override ada, nilai tersebut yang dipakai; bila tidak ada, tetap menggunakan
  nilai otomatis (tanpa memecah backward compatibility).
- `DirectIncomeItem` di `app/schemas/simulation.py`: tambah field `expense_category_id`,
  `auto_total`, dan `is_overridden`.
- `DirectIncomeSimulation` di `app/schemas/simulation.py`: tambah field `total_auto`.
- Relationship `direct_income_overrides` ditambahkan ke model `Organization` dan
  `ExpenseCategory`.

## [1.20.0] - 2026-06-08

### Ditambahkan
- Schema `DirectIncomeItem` dan `DirectIncomeSimulation` di `app/schemas/simulation.py`.
- Fungsi `simulate_direct_income()` di `app/services/simulation.py`: menghasilkan
  rincian per expense category yang ber-flag Direct Income beserta kategori pendapatan
  tujuannya. Hanya mengakumulasi nilai Yayasan — BoS tidak ikut karena sudah
  diperhitungkan di endpoint `bos-income`.
- Endpoint `GET /organizations/{org_id}/simulation/direct-income` (khusus UNIT).

## [1.19.0] - 2026-06-08

### Ditambahkan
- Endpoint `GET /organizations/{org_id}/simulation/bos-income` untuk simulasi
  detail pendapatan BoS (khusus UNIT): merinci kolom Dana BoS per kategori biaya
  operasional dan per kategori investasi, lengkap dengan subtotal per seksi dan
  total keseluruhan.
- Schema `BosIncomeLineItem` dan `BosIncomeSimulation` di `app/schemas/simulation.py`.
- Fungsi `simulate_bos_income()` di `app/services/simulation.py`.

## [1.18.0] - 2026-06-08

### Ditambahkan
- Kolom **Dana BoS** pada entri investasi aset tetap. Nilai BoS otomatis
  dimasukkan ke total Pendapatan BoS pada simulasi pendapatan (konsisten
  dengan pola biaya operasional/non-operasional). Beban akrual (depresiasi)
  tetap dihitung dari harga perolehan penuh.
- Migrasi ringan `ALTER TABLE investments ADD COLUMN bos` agar database lama
  kompatibel tanpa perlu reset.

## [1.17.0] - 2026-06-03

### Diubah
- Tarif UP unit kini meng-cover **depresiasi tahun berjalan investasi baru**
  Cabang/Pusat (alokasi proporsional siswa baru), sebelumnya hanya depresiasi
  aset lama induk. Ditambahkan field `cabang/pusat_allocated_new_investment_dep`
  pada simulasi UP.
- Pendapatan kontribusi Cabang/Pusat kini **berbasis alokasi**, bukan persentase:
  pendapatan induk = total setoran unit = porsi beban induk (UP+US) + depresiasi
  tahun berjalan induk. Setoran ini identik dengan beban alokasi yang ditanggung
  unit, sehingga buku unit & induk terkonsolidasi 1:1. Tarif kontribusi persen
  (`up_to_cabang`, dst.) tidak lagi dipakai untuk menghitung pendapatan induk.

## [1.16.0] - 2026-06-03

### Diubah
- Simulasi biaya unit kini memasukkan beban yang dialokasikan dari induk sebagai
  penambah beban operasional unit:
  - seluruh beban Cabang & Pusat yang dialokasikan ke unit (komponen UP & US),
  - depresiasi investasi baru tahun berjalan Cabang & Pusat (alokasi
    proporsional new_students), dan
  - depresiasi aset lama tahun berjalan Cabang & Pusat (alokasi proporsional
    new_students).

## [1.15.1] - 2026-06-03

### Diperbaiki
- User non-admin (organisasi) kini bisa membaca kategori referensi. Endpoint
  `GET /expense-categories`, `/income-categories`, dan `/investment-categories`
  sebelumnya dibatasi admin sehingga biaya operasional & non-operasional (serta
  kategori pendapatan/investasi) tidak muncul di halaman entri. Operasi tulis
  (create/update/delete/seed) tetap khusus admin.

## [1.15.0] - 2026-06-03

### Diubah
- User organisasi dapat memperbarui saldo kas & setara kas organisasinya sendiri.

## [1.14.0] - 2026-06-03

### Ditambahkan
- Endpoint reset password untuk akun login organisasi.

## [1.13.0] - 2026-06-02

### Ditambahkan
- Fitur menyalin Kategori Biaya UP/US antar organisasi.

## [1.12.0] - 2026-06-02

### Ditambahkan
- Saldo kas & setara kas per organisasi untuk perhitungan budget kas.

## [1.11.0] - 2026-06-02

### Diubah
- Uraian komponen pada simulasi memakai label kategori, bukan kode akun.

## [1.10.0] - 2026-06-02

### Ditambahkan
- Mekanisme subsidi dari Cabang/Pusat ke unit.

## [1.9.0] - 2026-06-02

### Diubah
- Override tarif UP dipakai apa adanya sebagai tarif final.

## [1.8.0] - 2026-06-02

### Ditambahkan
- Versi pendapatan otomatis beserta override pada simulasi.

## [1.7.0] - 2026-06-02

### Diubah
- Pisahkan alokasi Cabang dari Pusat pada UP & US unit.

## [1.6.0] - 2026-06-02

### Ditambahkan
- Alokasi depresiasi aset lama Cabang/Pusat ke komponen UP unit.

## [1.5.0] - 2026-05-29

### Diperbaiki
- Kalkulasi kontribusi UP/US pada simulasi pendapatan CABANG/PUSAT.

## [1.4.0] - 2026-05-29

### Diubah
- Pisahkan `allocated_components` dari `components` pada simulasi UP dan US.

## [1.3.0] - 2026-05-29

### Diperbaiki
- Kalkulasi UP: depresiasi selalu memengaruhi tarif meskipun ada override.

## [1.2.0] - 2026-05-29

### Ditambahkan
- Depresiasi aset lama ke komponen UP.

## [1.1.0] - 2026-05-29

### Ditambahkan
- Kode akun lengkap sebagai data referensi.

### Diubah
- `seed_defaults` menjadi additive (tidak menghapus data yang sudah ada).

## [1.0.1] - 2026-05-29

### Diperbaiki
- Bersihkan lint error: hapus import dan variabel yang tidak terpakai.

## [1.0.0] - 2026-05-29

### Ditambahkan
- Rilis pertama Budget Backend YPII.

[Unreleased]: https://github.com/cakrawala-tumbuh/budget-sekolah-backend/compare/v1.21.1...HEAD
[1.21.1]: https://github.com/cakrawala-tumbuh/budget-sekolah-backend/compare/v1.21.0...v1.21.1
[1.18.0]: https://github.com/cakrawala-tumbuh/budget-sekolah-backend/compare/v1.17.0...v1.18.0
[1.17.0]: https://github.com/cakrawala-tumbuh/budget-sekolah-backend/compare/v1.15.1...v1.17.0
[1.15.1]: https://github.com/cakrawala-tumbuh/budget-sekolah-backend/compare/v1.15.0...v1.15.1
[1.15.0]: https://github.com/cakrawala-tumbuh/budget-sekolah-backend/compare/v1.14.0...v1.15.0
[1.14.0]: https://github.com/cakrawala-tumbuh/budget-sekolah-backend/compare/v1.13.0...v1.14.0
[1.13.0]: https://github.com/cakrawala-tumbuh/budget-sekolah-backend/compare/v1.12.0...v1.13.0
[1.12.0]: https://github.com/cakrawala-tumbuh/budget-sekolah-backend/compare/v1.11.0...v1.12.0
[1.11.0]: https://github.com/cakrawala-tumbuh/budget-sekolah-backend/compare/v1.10.0...v1.11.0
[1.10.0]: https://github.com/cakrawala-tumbuh/budget-sekolah-backend/compare/v1.9.0...v1.10.0
[1.9.0]: https://github.com/cakrawala-tumbuh/budget-sekolah-backend/compare/v1.8.0...v1.9.0
[1.8.0]: https://github.com/cakrawala-tumbuh/budget-sekolah-backend/compare/v1.7.0...v1.8.0
[1.7.0]: https://github.com/cakrawala-tumbuh/budget-sekolah-backend/compare/v1.6.0...v1.7.0
[1.6.0]: https://github.com/cakrawala-tumbuh/budget-sekolah-backend/compare/v1.5.0...v1.6.0
[1.5.0]: https://github.com/cakrawala-tumbuh/budget-sekolah-backend/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/cakrawala-tumbuh/budget-sekolah-backend/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/cakrawala-tumbuh/budget-sekolah-backend/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/cakrawala-tumbuh/budget-sekolah-backend/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/cakrawala-tumbuh/budget-sekolah-backend/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/cakrawala-tumbuh/budget-sekolah-backend/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/cakrawala-tumbuh/budget-sekolah-backend/releases/tag/v1.0.0
