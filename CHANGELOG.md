# Changelog

Semua perubahan penting pada proyek ini didokumentasikan di berkas ini.

Format mengacu pada [Keep a Changelog](https://keepachangelog.com/id/1.1.0/),
dan proyek ini menganut [Semantic Versioning](https://semver.org/lang/id/).

## [Unreleased]

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

[Unreleased]: https://github.com/cakrawala-tumbuh/budget-sekolah-backend/compare/v1.18.0...HEAD
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
