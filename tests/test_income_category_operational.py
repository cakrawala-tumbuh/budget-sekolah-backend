"""
Test `IncomeCategory.is_operational` — kolom penanda operasional/non-operasional
pada kategori pendapatan, padanan `ExpenseCategory.is_operational`.

Cakupan sesuai `## Skenario Uji` issue cakrawala-tumbuh/budget-sekolah-backend#1:
  - Create tanpa `is_operational` -> default True.
  - PUT mengubah `is_operational` dan perubahannya bertahan.
  - Item `simulate_income` membawa `is_operational` sesuai kategori sumbernya.
  - Migrasi ringan pada DB lama menambah kolom dan mengisi seluruh baris True.
  - Migrasi ringan idempoten (dijalankan dua kali tidak error, tidak mengubah nilai).
  - Mengubah `is_operational` tidak mengubah `total` yang dihitung simulasi.
"""
from fastapi import status
from sqlalchemy import create_engine, inspect, text


# ── Helpers ──────────────────────────────────────────────────────────────────

def _income_cat_id(client, code: str) -> int:
    cats = client.get("/income-categories").json()
    return next(c["id"] for c in cats if c["code"] == code)


def _create_unit(client, code: str):
    return client.post("/organizations", json={
        "code": code, "name": f"SD {code}", "org_type": "UNIT",
    }).json()["id"]


# ── Skema: create/update ──────────────────────────────────────────────────────

class TestIncomeCategoryOperationalSchema:
    def test_create_without_is_operational_defaults_true(self, client):
        resp = client.post("/income-categories", json={
            "code": "9100.01", "label": "Kategori Uji",
        })
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["is_operational"] is True

    def test_list_exposes_is_operational_for_every_category(self, client):
        cats = client.get("/income-categories").json()
        assert cats, "kategori pendapatan bawaan harus sudah ter-seed"
        for cat in cats:
            assert "is_operational" in cat

    def test_put_updates_is_operational_and_persists(self, client):
        cat_id = _income_cat_id(client, "4620.01")  # Pendapatan Lain-lain (MANUAL)

        resp = client.put(f"/income-categories/{cat_id}", json={"is_operational": False})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["is_operational"] is False

        # GET ulang membuktikan perubahan bertahan, bukan cuma respons PUT
        again = client.get(f"/income-categories/{cat_id}")
        assert again.json()["is_operational"] is False

        # Kembalikan ke True supaya tidak membocorkan state ke test lain
        # yang berbagi engine_fixture (meski tiap test punya transaksi
        # tersendiri, sisipkan untuk kejelasan niat).
        restore = client.put(f"/income-categories/{cat_id}", json={"is_operational": True})
        assert restore.json()["is_operational"] is True


# ── Item hasil simulasi pendapatan ────────────────────────────────────────────

class TestIncomeSimulationOperationalFlag:
    def test_up_and_us_items_are_operational_by_default(self, client):
        """UP (4110.01) dan US (4120.01) bawaan sudah di-seed is_operational=True."""
        org_id = _create_unit(client, "SIM-OP-1")
        data = client.get(f"/organizations/{org_id}/simulation/income").json()

        up_items = [i for i in data["items"] if i["account_code"] == "4110.01"]
        us_items = [i for i in data["items"] if i["account_code"] == "4120.01"]
        assert up_items and up_items[0]["is_operational"] is True
        assert us_items and us_items[0]["is_operational"] is True

    def test_manual_income_item_carries_source_category_flag(self, client):
        """Item pendapatan manual membawa is_operational persis dari kategorinya."""
        org_id = _create_unit(client, "SIM-OP-2")
        cat_id = _income_cat_id(client, "4620.01")  # Pendapatan Lain-lain (MANUAL)

        client.post(f"/organizations/{org_id}/income-entries", json={
            "income_category_id": cat_id, "description": "Lain-lain", "amount": 5_000_000.0,
        })

        before = client.get(f"/organizations/{org_id}/simulation/income").json()
        item_before = next(i for i in before["items"] if i["account_code"] == "4620.01")
        assert item_before["is_operational"] is True

        # Tandai kategori sebagai non-operasional lewat PUT yang sudah ada
        client.put(f"/income-categories/{cat_id}", json={"is_operational": False})

        after = client.get(f"/organizations/{org_id}/simulation/income").json()
        item_after = next(i for i in after["items"] if i["account_code"] == "4620.01")
        assert item_after["is_operational"] is False

        # Kembalikan state
        client.put(f"/income-categories/{cat_id}", json={"is_operational": True})

    def test_toggling_is_operational_does_not_change_total(self, client):
        """Mengubah is_operational adalah metadata murni — total simulasi tak berubah."""
        org_id = _create_unit(client, "SIM-OP-3")
        cat_id = _income_cat_id(client, "4610.02")  # Sumbangan Lain (MANUAL)

        client.post(f"/organizations/{org_id}/income-entries", json={
            "income_category_id": cat_id, "description": "Sumbangan", "amount": 7_500_000.0,
        })

        before = client.get(f"/organizations/{org_id}/simulation/income").json()

        client.put(f"/income-categories/{cat_id}", json={"is_operational": False})
        after = client.get(f"/organizations/{org_id}/simulation/income").json()

        assert after["total"] == before["total"]
        assert after["total_auto"] == before["total_auto"]

        client.put(f"/income-categories/{cat_id}", json={"is_operational": True})

    def test_simulate_summary_total_unaffected_by_operational_flag(self, client):
        """simulate_summary (dikonsumsi laporan RAB) tidak berubah nilainya."""
        org_id = _create_unit(client, "SIM-OP-4")
        cat_id = _income_cat_id(client, "4610.01")  # Sumbangan Pembangunan (MANUAL)

        client.post(f"/organizations/{org_id}/income-entries", json={
            "income_category_id": cat_id, "description": "Sumbangan Pembangunan",
            "amount": 3_000_000.0,
        })

        before = client.get(f"/organizations/{org_id}/simulation/summary").json()
        client.put(f"/income-categories/{cat_id}", json={"is_operational": False})
        after = client.get(f"/organizations/{org_id}/simulation/summary").json()

        assert after["total_cash_revenue"] == before["total_cash_revenue"]

        client.put(f"/income-categories/{cat_id}", json={"is_operational": True})


# ── Migrasi ringan (`_run_lightweight_migrations`) ────────────────────────────

class TestLightweightMigrationIncomeOperational:
    """
    `_run_lightweight_migrations()` (app/main.py) memakai `engine` di level modul
    `app.main`. Test ini memasang engine SQLite in-memory bergaya "DB lama" —
    tabel `income_categories` tanpa kolom `is_operational` — lalu memverifikasi
    migrasinya menambah kolom, mengisi seluruh baris True, dan idempoten.
    """

    def _legacy_engine(self):
        eng = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        with eng.begin() as conn:
            conn.execute(text("CREATE TABLE organizations (id INTEGER PRIMARY KEY)"))
            conn.execute(text(
                "CREATE TABLE income_categories ("
                "id INTEGER PRIMARY KEY, "
                "code VARCHAR(20) NOT NULL UNIQUE, "
                "label VARCHAR(200) NOT NULL, "
                "calc_method VARCHAR(20) NOT NULL DEFAULT 'MANUAL', "
                "sort_order INTEGER DEFAULT 0)"
            ))
            conn.execute(text(
                "INSERT INTO income_categories (code, label) "
                "VALUES ('4110.01', 'Uang Pangkal (UP)')"
            ))
            conn.execute(text(
                "INSERT INTO income_categories (code, label) "
                "VALUES ('4620.01', 'Pendapatan Lain-lain')"
            ))
        return eng

    def test_migration_adds_column_and_backfills_true(self, monkeypatch):
        import app.main as main_module

        eng = self._legacy_engine()
        monkeypatch.setattr(main_module, "engine", eng)

        main_module._run_lightweight_migrations()

        inspector = inspect(eng)
        columns = {c["name"] for c in inspector.get_columns("income_categories")}
        assert "is_operational" in columns

        with eng.connect() as conn:
            rows = conn.execute(
                text("SELECT code, is_operational FROM income_categories")
            ).fetchall()
        assert len(rows) == 2
        assert all(row[1] == 1 for row in rows)

        eng.dispose()

    def test_migration_is_idempotent(self, monkeypatch):
        import app.main as main_module

        eng = self._legacy_engine()
        monkeypatch.setattr(main_module, "engine", eng)

        main_module._run_lightweight_migrations()
        # Jalankan lagi — tidak boleh melempar exception (kolom sudah ada)
        main_module._run_lightweight_migrations()

        with eng.connect() as conn:
            rows = conn.execute(
                text("SELECT code, is_operational FROM income_categories")
            ).fetchall()
        assert len(rows) == 2
        assert all(row[1] == 1 for row in rows)

        eng.dispose()

    def test_migration_does_not_overwrite_existing_values(self, monkeypatch):
        """Sekali kolom ada, migrasi ulang tidak boleh mereset nilai yang sudah diubah."""
        import app.main as main_module

        eng = self._legacy_engine()
        monkeypatch.setattr(main_module, "engine", eng)

        main_module._run_lightweight_migrations()
        with eng.begin() as conn:
            conn.execute(text(
                "UPDATE income_categories SET is_operational = 0 WHERE code = '4620.01'"
            ))

        main_module._run_lightweight_migrations()

        with eng.connect() as conn:
            row = conn.execute(
                text("SELECT is_operational FROM income_categories WHERE code = '4620.01'")
            ).fetchone()
        assert row[0] == 0

        eng.dispose()
