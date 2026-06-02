"""
RAB simulation tests — UP, US, Income, Expenses, Depreciation, Summary.

Scenario: a simple school with data that is easy to verify by hand.
"""

from fastapi import status


def _expense_cat_id(client, code: str) -> int:
    cats = client.get("/expense-categories").json()
    return next(c["id"] for c in cats if c["code"] == code)


def _invest_cat_id(client, code: str) -> int:
    cats = client.get("/investment-categories").json()
    return next(c["id"] for c in cats if c["code"] == code)


def _setup_unit(client, code: str):
    """Create a unit with minimal data for simulation tests."""
    org_id = client.post("/organizations", json={
        "code": code, "name": f"SD Simulasi {code}", "org_type": "UNIT",
    }).json()["id"]

    # Student assumptions
    client.put(f"/organizations/{org_id}/assumption", json={
        "grade_1": 60, "grade_2": 58, "grade_3": 55,
        "grade_4": 52, "grade_5": 50, "grade_6": 51,
        "new_student_count": 60, "returning_student_count": 266,
        "staff_count": 24,
    })

    # Salary expense (5110.01) — not UP, not direct-income -> goes into US
    cat_gaji = _expense_cat_id(client, "5110.01")
    client.post(f"/organizations/{org_id}/budget-entries", json={
        "expense_category_id": cat_gaji, "line_number": 1,
        "description": "Gaji", "foundation": 1_008_000_000.0, "bos": 0.0,
    })

    # HR development (5130.01) -> goes into UP
    cat_pengabdian = _expense_cat_id(client, "5130.01")
    client.post(f"/organizations/{org_id}/budget-entries", json={
        "expense_category_id": cat_pengabdian, "line_number": 1,
        "description": "Pengabdian", "foundation": 36_000_000.0, "bos": 0.0,
    })

    return org_id


class TestUPSimulation:
    def test_up_calculates_correctly(self, client):
        org_id = _setup_unit(client, "SD-SIM-UP")
        resp = client.get(f"/organizations/{org_id}/simulation/up")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        # Only 5130.01 = 36_000_000; no investments -> total_up_cost = 36_000_000
        assert data["total_up_cost"] == 36_000_000.0
        assert data["new_investment_dep"] == 0.0
        assert data["old_asset_dep"] == 0.0
        # auto_up_rate = 36_000_000 / 60 = 600_000
        assert data["auto_up_rate"] == 600_000.0
        assert data["total_up_revenue"] == 36_000_000.0

    def test_up_includes_old_asset_depreciation(self, client):
        org_id = _setup_unit(client, "SD-SIM-UP4")
        # Existing asset: 8_000_000 / 4 years, acquired 2024 -> dep_current_year = 2_000_000
        client.post(f"/organizations/{org_id}/depreciation", json={
            "asset_name": "Komputer Lama", "acquisition_cost": 8_000_000.0,
            "useful_life": 4, "acquisition_year": 2024,
        })
        resp = client.get(f"/organizations/{org_id}/simulation/up")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["old_asset_dep"] == 2_000_000.0
        # total_up_cost_with_dep = 36_000_000 + 0 (no new inv) + 2_000_000
        assert data["total_up_cost_with_dep"] == 38_000_000.0
        # auto_up_rate = 38_000_000 / 60
        assert abs(data["auto_up_rate"] - 38_000_000.0 / 60) < 1.0

    def test_up_with_override(self, client):
        org_id = _setup_unit(client, "SD-SIM-UP2")
        client.put(f"/organizations/{org_id}/assumption", json={
            "grade_1": 60, "grade_2": 0, "grade_3": 0,
            "grade_4": 0, "grade_5": 0, "grade_6": 0,
            "new_student_count": 60, "returning_student_count": 0,
            "staff_count": 5,
            "override_up_rate": 1_000_000.0,
        })
        resp = client.get(f"/organizations/{org_id}/simulation/up")
        data = resp.json()
        # Tidak ada depresiasi: final_up_rate = override + 0 = override
        assert data["new_investment_dep"] == 0.0
        assert data["old_asset_dep"] == 0.0
        assert data["final_up_rate"] == 1_000_000.0
        assert data["total_up_revenue"] == 60_000_000.0

    def test_up_override_is_final_rate_without_dep(self, client):
        """Override tarif UP adalah tarif final; depresiasi TIDAK ditambahkan di atasnya."""
        org_id = _setup_unit(client, "SD-SIM-UP5")
        # Set override
        client.put(f"/organizations/{org_id}/assumption", json={
            "grade_1": 60, "grade_2": 0, "grade_3": 0,
            "grade_4": 0, "grade_5": 0, "grade_6": 0,
            "new_student_count": 60, "returning_student_count": 0,
            "staff_count": 5,
            "override_up_rate": 1_000_000.0,
        })
        # Old asset: 12_000_000 / 4 years, acquired 2024 -> dep_current_year = 3_000_000
        client.post(f"/organizations/{org_id}/depreciation", json={
            "asset_name": "Komputer Lama", "acquisition_cost": 12_000_000.0,
            "useful_life": 4, "acquisition_year": 2024,
        })
        resp = client.get(f"/organizations/{org_id}/simulation/up")
        data = resp.json()
        # Depresiasi tetap dilaporkan & masuk tarif otomatis: (36jt + 3jt)/60 = 650rb.
        assert data["old_asset_dep"] == 3_000_000.0
        assert abs(data["auto_up_rate"] - 650_000.0) < 1.0
        # ...tetapi tarif & pendapatan final memakai override apa adanya (tanpa dep).
        assert data["final_up_rate"] == 1_000_000.0
        assert abs(data["total_up_revenue"] - 1_000_000.0 * 60) < 1.0

    def test_up_only_for_unit(self, client):
        cabang = client.post("/organizations", json={
            "code": "CBG-SIM-UP", "name": "Cabang UP Test", "org_type": "CABANG",
        }).json()
        resp = client.get(f"/organizations/{cabang['id']}/simulation/up")
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUSSimulation:
    def test_us_calculates_correctly(self, client):
        org_id = _setup_unit(client, "SD-SIM-US")
        resp = client.get(f"/organizations/{org_id}/simulation/us")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        # 5110.01 = 1_008_000_000 goes into US; 5130.01 does not
        assert data["total_us_cost"] == 1_008_000_000.0
        # tarif_us = 1_008_000_000 / (326 x 12)
        expected_tarif = 1_008_000_000.0 / (326 * 12)
        assert abs(data["auto_us_rate"] - expected_tarif) < 1.0


class TestExpenseSimulation:
    def test_expenses_split_correctly(self, client):
        org_id = _setup_unit(client, "SD-SIM-EXP")
        # Tambah biaya non-operasional
        cat_id = _expense_cat_id(client, "5590.01")
        client.post(f"/organizations/{org_id}/budget-entries", json={
            "expense_category_id": cat_id, "line_number": 1,
            "description": "Kontribusi UP ke Pusat", "foundation": 1_440_000.0, "bos": 0.0,
        })
        resp = client.get(f"/organizations/{org_id}/simulation/expenses")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["total_operational"] > 0
        assert data["total_non_operational"] > 0
        assert abs(data["total"] - (data["total_operational"] + data["total_non_operational"])) < 0.01


class TestDepreciationSimulation:
    def test_depreciation_new_and_old(self, client):
        org_id = _setup_unit(client, "SD-SIM-DEP")
        # New asset
        inv_cat_id = _invest_cat_id(client, "1330.02")
        client.post(f"/organizations/{org_id}/investments", json={
            "investment_category_id": inv_cat_id, "asset_name": "Laptop",
            "purchase_price": 12_000_000.0, "useful_life": 4, "start_month": 7,
        })
        # Existing asset
        client.post(f"/organizations/{org_id}/depreciation", json={
            "asset_name": "Komputer Lama", "acquisition_cost": 8_000_000.0,
            "useful_life": 4, "acquisition_year": 2023,
        })
        resp = client.get(f"/organizations/{org_id}/simulation/depreciation")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data["items"]) == 2
        sources = {i["source"] for i in data["items"]}
        assert sources == {"new", "existing"}
        assert data["total_current_year_dep"] > 0


class TestBudgetSummary:
    def test_summary_structure(self, client):
        org_id = _setup_unit(client, "SD-SIM-SUM")
        resp = client.get(f"/organizations/{org_id}/simulation/summary")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        required_keys = {
            "organization_id", "organization_name", "org_type", "budget_year",
            "total_cash_revenue", "total_cash_expenses", "cash_surplus_deficit",
            "total_accrual_expenses", "accrual_surplus_deficit",
            "income", "expenses", "depreciation",
        }
        assert required_keys.issubset(data.keys())

    def test_surplus_defisit_kas_formula(self, client):
        org_id = _setup_unit(client, "SD-SIM-SUM2")
        resp = client.get(f"/organizations/{org_id}/simulation/summary")
        data = resp.json()
        expected = data["total_cash_revenue"] - data["total_cash_expenses"]
        assert abs(data["cash_surplus_deficit"] - expected) < 0.01

    def test_accrual_includes_depreciation(self, client):
        org_id = _setup_unit(client, "SD-SIM-SUM3")
        inv_cat_id = _invest_cat_id(client, "1330.02")
        client.post(f"/organizations/{org_id}/investments", json={
            "investment_category_id": inv_cat_id, "asset_name": "Laptop",
            "purchase_price": 12_000_000.0, "useful_life": 4, "start_month": 7,
        })
        resp = client.get(f"/organizations/{org_id}/simulation/summary")
        data = resp.json()
        # accrual expenses = cash expenses + depreciation
        expected_accrual = data["total_cash_expenses"] + data["depreciation"]["total_current_year_dep"]
        assert abs(data["total_accrual_expenses"] - expected_accrual) < 0.01


class TestCabangIncomeSimulation:
    """Pendapatan CABANG berasal dari kontribusi UP/US setiap child UNIT."""

    def _setup_cabang_with_unit(self, client, suffix: str):
        """Buat CABANG dan satu child UNIT dengan data lengkap, lalu daftarkan alokasi."""
        cabang_id = client.post("/organizations", json={
            "code": f"CBG-INC-{suffix}", "name": f"Cabang Income {suffix}", "org_type": "CABANG",
        }).json()["id"]

        unit_id = _setup_unit(client, f"SD-CBG-INC-{suffix}")

        # Tarif kontribusi unit: UP 12% ke cabang, US 10% ke cabang
        client.put(f"/organizations/{unit_id}/contribution-rates", json={
            "up_to_pusat": 0.04, "up_to_cabang": 0.12,
            "us_to_pusat": 0.05, "us_to_cabang": 0.10,
            "development_fund": 0.20, "deficit_reserve": 0.05,
            "social_care": 0.03, "teacher_study": 0.03,
        })

        # Daftarkan unit sebagai kontributor ke cabang
        client.put(f"/organizations/{cabang_id}/contribution-allocations", json={
            "from_organization_id": unit_id,
            "total_students": 326,
            "new_students": 60,
        })
        return cabang_id, unit_id

    def test_cabang_income_uses_unit_up_us_revenue(self, client):
        """Kontribusi UP/US ke CABANG = revenue aktual unit × tarif unit, bukan pengeluaran cabang."""
        cabang_id, unit_id = self._setup_cabang_with_unit(client, "A")

        up_revenue = client.get(f"/organizations/{unit_id}/simulation/up").json()["total_up_revenue"]
        us_revenue = client.get(f"/organizations/{unit_id}/simulation/us").json()["total_us_revenue"]
        expected_up = up_revenue * 0.12
        expected_us = us_revenue * 0.10

        resp = client.get(f"/organizations/{cabang_id}/simulation/income")
        assert resp.status_code == 200
        data = resp.json()

        total_up = sum(i["total"] for i in data["items"] if i["account_code"] == "4630.01")
        total_us = sum(i["total"] for i in data["items"] if i["account_code"] == "4630.02")
        assert abs(total_up - expected_up) < 1.0
        assert abs(total_us - expected_us) < 1.0
        assert abs(data["total"] - (expected_up + expected_us)) < 1.0

    def test_cabang_income_zero_without_allocations(self, client):
        """CABANG tanpa child unit terdaftar menghasilkan total pendapatan 0."""
        cabang_id = client.post("/organizations", json={
            "code": "CBG-EMPTY", "name": "Cabang Kosong", "org_type": "CABANG",
        }).json()["id"]
        resp = client.get(f"/organizations/{cabang_id}/simulation/income")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0.0

    def test_allocation_simulation_uses_unit_revenue(self, client):
        """simulate_allocation menampilkan kontribusi berdasarkan revenue aktual unit."""
        cabang_id, unit_id = self._setup_cabang_with_unit(client, "B")

        up_revenue = client.get(f"/organizations/{unit_id}/simulation/up").json()["total_up_revenue"]
        us_revenue = client.get(f"/organizations/{unit_id}/simulation/us").json()["total_us_revenue"]

        resp = client.get(f"/organizations/{cabang_id}/simulation/allocation")
        assert resp.status_code == 200
        data = resp.json()

        assert len(data["units"]) == 1
        u = data["units"][0]
        assert abs(u["contribution_up"] - up_revenue * 0.12) < 1.0
        assert abs(u["contribution_us"] - us_revenue * 0.10) < 1.0
        # total_base_cost_up/us = total pool revenue dari semua unit
        assert abs(data["total_base_cost_up"] - up_revenue) < 1.0
        assert abs(data["total_base_cost_us"] - us_revenue) < 1.0


class TestParentDepreciationAllocation:
    """
    Depresiasi aset lama tahun ini di Cabang/Pusat menambah alokasi UP unit.

    Aset lama induk (Cabang/Pusat) yang masih disusutkan tahun berjalan
    didistribusikan ke unit secara proporsional berdasarkan new_students,
    lalu menambah beban UP unit (di luar komponen biaya UP unit sendiri).
    """

    def _make_unit(self, client, code: str, parent_id: int) -> int:
        org_id = client.post("/organizations", json={
            "code": code, "name": f"SD {code}", "org_type": "UNIT",
            "parent_id": parent_id,
        }).json()["id"]
        client.put(f"/organizations/{org_id}/assumption", json={
            "grade_1": 60, "grade_2": 0, "grade_3": 0, "grade_4": 0,
            "grade_5": 0, "grade_6": 0,
            "new_student_count": 60, "returning_student_count": 0, "staff_count": 5,
        })
        # 5130.01 -> komponen UP = 36_000_000
        cat = _expense_cat_id(client, "5130.01")
        client.post(f"/organizations/{org_id}/budget-entries", json={
            "expense_category_id": cat, "line_number": 1,
            "description": "Pengabdian", "foundation": 36_000_000.0, "bos": 0.0,
        })
        return org_id

    def _add_old_asset(self, client, org_id: int, cost: float,
                       year: int = 2024, life: int = 4, name: str = "Aset Lama Induk"):
        return client.post(f"/organizations/{org_id}/depreciation", json={
            "asset_name": name, "acquisition_cost": cost,
            "useful_life": life, "acquisition_year": year,
        })

    def _register(self, client, parent_id: int, unit_id: int, new_students: int,
                  total_students: int = 326, **extra):
        return client.put(f"/organizations/{parent_id}/contribution-allocations", json={
            "from_organization_id": unit_id,
            "total_students": total_students,
            "new_students": new_students,
            **extra,
        })

    def test_cabang_old_asset_dep_adds_to_unit_up(self, client):
        pusat = client.post("/organizations", json={
            "code": "PST-DEP-A", "name": "Pusat A", "org_type": "PUSAT",
        }).json()["id"]
        cabang = client.post("/organizations", json={
            "code": "CBG-DEP-A", "name": "Cabang A", "org_type": "CABANG",
            "parent_id": pusat,
        }).json()["id"]
        unit = self._make_unit(client, "SD-DEP-A", cabang)
        # Unit satu-satunya kontributor cabang -> pct_up = 1.0
        self._register(client, cabang, unit, new_students=60)
        # Aset lama cabang: 12_000_000 / 4 -> dep tahun ini = 3_000_000
        self._add_old_asset(client, cabang, 12_000_000.0)

        data = client.get(f"/organizations/{unit}/simulation/up").json()
        # Depresiasi berasal dari Cabang; bucket Pusat nol
        assert data["cabang_allocated_old_asset_dep"] == 3_000_000.0
        assert data["pusat_allocated_old_asset_dep"] == 0.0
        # Komponen biaya UP unit murni 36 jt (tidak termasuk dep induk)
        assert data["total_up_cost"] == 36_000_000.0
        assert data["old_asset_dep"] == 0.0
        assert data["total_up_cost_with_dep"] == 39_000_000.0
        assert abs(data["final_up_rate"] - 39_000_000.0 / 60) < 1.0

    def test_pusat_and_cabang_dep_both_allocated(self, client):
        pusat = client.post("/organizations", json={
            "code": "PST-DEP-B", "name": "Pusat B", "org_type": "PUSAT",
        }).json()["id"]
        cabang = client.post("/organizations", json={
            "code": "CBG-DEP-B", "name": "Cabang B", "org_type": "CABANG",
            "parent_id": pusat,
        }).json()["id"]
        unit = self._make_unit(client, "SD-DEP-B", cabang)
        # Unit terdaftar sebagai kontributor di cabang dan pusat (pct_up = 1.0 keduanya)
        self._register(client, cabang, unit, new_students=60)
        self._register(client, pusat, unit, new_students=60)
        # Cabang: 12_000_000 / 4 -> 3_000_000 ; Pusat: 8_000_000 / 4 -> 2_000_000
        self._add_old_asset(client, cabang, 12_000_000.0)
        self._add_old_asset(client, pusat, 8_000_000.0)

        data = client.get(f"/organizations/{unit}/simulation/up").json()
        # Alokasi depresiasi Cabang dan Pusat dipisahkan
        assert data["cabang_allocated_old_asset_dep"] == 3_000_000.0
        assert data["pusat_allocated_old_asset_dep"] == 2_000_000.0
        assert data["total_up_cost_with_dep"] == 41_000_000.0

    def test_dep_split_proportionally_between_units(self, client):
        cabang = client.post("/organizations", json={
            "code": "CBG-DEP-C", "name": "Cabang C", "org_type": "CABANG",
        }).json()["id"]
        unit_a = self._make_unit(client, "SD-DEP-C1", cabang)
        unit_b = self._make_unit(client, "SD-DEP-C2", cabang)
        # Proporsi new_students: A=60, B=40 dari total 100 -> 0.6 / 0.4
        self._register(client, cabang, unit_a, new_students=60)
        self._register(client, cabang, unit_b, new_students=40)
        # Aset lama cabang: 12_000_000 / 4 -> dep tahun ini = 3_000_000
        self._add_old_asset(client, cabang, 12_000_000.0)

        data_a = client.get(f"/organizations/{unit_a}/simulation/up").json()
        data_b = client.get(f"/organizations/{unit_b}/simulation/up").json()
        assert abs(data_a["cabang_allocated_old_asset_dep"] - 1_800_000.0) < 1.0
        assert abs(data_b["cabang_allocated_old_asset_dep"] - 1_200_000.0) < 1.0

    def test_override_pct_up_respected(self, client):
        cabang = client.post("/organizations", json={
            "code": "CBG-DEP-D", "name": "Cabang D", "org_type": "CABANG",
        }).json()["id"]
        unit = self._make_unit(client, "SD-DEP-D", cabang)
        # Override proporsi UP unit ke 0.25
        self._register(client, cabang, unit, new_students=60, override_pct_up=0.25)
        # Aset lama cabang: 12_000_000 / 4 -> 3_000_000 ; 0.25 * 3_000_000 = 750_000
        self._add_old_asset(client, cabang, 12_000_000.0)

        data = client.get(f"/organizations/{unit}/simulation/up").json()
        assert abs(data["cabang_allocated_old_asset_dep"] - 750_000.0) < 1.0

    def test_override_up_rate_ignores_parent_dep(self, client):
        """Override tarif UP adalah tarif final; dep induk tidak ditambahkan ke tarif final."""
        cabang = client.post("/organizations", json={
            "code": "CBG-DEP-E", "name": "Cabang E", "org_type": "CABANG",
        }).json()["id"]
        unit = self._make_unit(client, "SD-DEP-E", cabang)
        client.put(f"/organizations/{unit}/assumption", json={
            "grade_1": 60, "grade_2": 0, "grade_3": 0, "grade_4": 0,
            "grade_5": 0, "grade_6": 0,
            "new_student_count": 60, "returning_student_count": 0, "staff_count": 5,
            "override_up_rate": 1_000_000.0,
        })
        self._register(client, cabang, unit, new_students=60)
        self._add_old_asset(client, cabang, 12_000_000.0)  # dep = 3_000_000

        data = client.get(f"/organizations/{unit}/simulation/up").json()
        # Dep induk tetap dialokasikan & masuk tarif otomatis: (36jt + 3jt)/60 = 650rb.
        assert data["cabang_allocated_old_asset_dep"] == 3_000_000.0
        assert abs(data["auto_up_rate"] - 650_000.0) < 1.0
        # ...tetapi tarif final memakai override apa adanya, tanpa tambahan dep.
        assert data["final_up_rate"] == 1_000_000.0

    def test_no_parent_dep_when_unit_unregistered(self, client):
        cabang = client.post("/organizations", json={
            "code": "CBG-DEP-F", "name": "Cabang F", "org_type": "CABANG",
        }).json()["id"]
        unit = self._make_unit(client, "SD-DEP-F", cabang)
        # Tidak didaftarkan ke contribution-allocations cabang
        self._add_old_asset(client, cabang, 12_000_000.0)

        data = client.get(f"/organizations/{unit}/simulation/up").json()
        assert data["cabang_allocated_old_asset_dep"] == 0.0
        assert data["pusat_allocated_old_asset_dep"] == 0.0

    def test_no_parent_dep_for_standalone_unit(self, client):
        """Unit tanpa induk tidak memperoleh alokasi depresiasi induk."""
        unit = _setup_unit(client, "SD-DEP-G")
        data = client.get(f"/organizations/{unit}/simulation/up").json()
        assert data["cabang_allocated_old_asset_dep"] == 0.0
        assert data["pusat_allocated_old_asset_dep"] == 0.0


class TestParentAllocationSeparation:
    """
    Alokasi biaya dari Cabang dipisahkan dari alokasi Pusat pada UP & US unit.

    Hierarki: PUSAT <- CABANG <- UNIT, dengan ParentExpenseAllocation di
    kedua induk. Unit terdaftar sebagai kontributor (sole) di Cabang dan Pusat.
    """

    def _setup(self, client, suffix: str):
        pusat = client.post("/organizations", json={
            "code": f"PST-SEP-{suffix}", "name": f"Pusat {suffix}", "org_type": "PUSAT",
        }).json()["id"]
        cabang = client.post("/organizations", json={
            "code": f"CBG-SEP-{suffix}", "name": f"Cabang {suffix}",
            "org_type": "CABANG", "parent_id": pusat,
        }).json()["id"]
        unit = client.post("/organizations", json={
            "code": f"SD-SEP-{suffix}", "name": f"SD {suffix}",
            "org_type": "UNIT", "parent_id": cabang,
        }).json()["id"]
        client.put(f"/organizations/{unit}/assumption", json={
            "grade_1": 60, "grade_2": 140, "grade_3": 0, "grade_4": 0,
            "grade_5": 0, "grade_6": 0,
            "new_student_count": 60, "returning_student_count": 140, "staff_count": 5,
        })

        cat_dev = _expense_cat_id(client, "5130.01")   # UP component
        cat_gaji = _expense_cat_id(client, "5110.01")  # US component

        # Biaya di Cabang: dev 24jt (UP), gaji 120jt (US)
        client.post(f"/organizations/{cabang}/budget-entries", json={
            "expense_category_id": cat_dev, "line_number": 1,
            "description": "Dev Cabang", "foundation": 24_000_000.0, "bos": 0.0,
        })
        client.post(f"/organizations/{cabang}/budget-entries", json={
            "expense_category_id": cat_gaji, "line_number": 1,
            "description": "Gaji Cabang", "foundation": 120_000_000.0, "bos": 0.0,
        })
        # Biaya di Pusat: dev 30jt (UP), gaji 90jt (US)
        client.post(f"/organizations/{pusat}/budget-entries", json={
            "expense_category_id": cat_dev, "line_number": 1,
            "description": "Dev Pusat", "foundation": 30_000_000.0, "bos": 0.0,
        })
        client.post(f"/organizations/{pusat}/budget-entries", json={
            "expense_category_id": cat_gaji, "line_number": 1,
            "description": "Gaji Pusat", "foundation": 90_000_000.0, "bos": 0.0,
        })

        # ParentExpenseAllocation di Cabang dan Pusat
        for parent in (cabang, pusat):
            client.post(f"/organizations/{parent}/parent-expense-allocations",
                        json={"expense_category_id": cat_dev, "affects_up": True})
            client.post(f"/organizations/{parent}/parent-expense-allocations",
                        json={"expense_category_id": cat_gaji, "affects_up": False})

        # Unit kontributor tunggal di Cabang dan Pusat -> pct = 1.0
        for parent in (cabang, pusat):
            client.put(f"/organizations/{parent}/contribution-allocations", json={
                "from_organization_id": unit, "total_students": 200, "new_students": 60,
            })
        return pusat, cabang, unit

    def test_up_separates_cabang_and_pusat(self, client):
        _, _, unit = self._setup(client, "UP")
        data = client.get(f"/organizations/{unit}/simulation/up").json()

        assert abs(data["cabang_allocated_up_cost"] - 24_000_000.0) < 1.0
        assert abs(data["pusat_allocated_up_cost"] - 30_000_000.0) < 1.0
        # total = own (0) + cabang + pusat
        assert abs(data["total_up_cost"] - 54_000_000.0) < 1.0

        cabang_items = data["cabang_allocated_components"]
        pusat_items = data["pusat_allocated_components"]
        assert len(cabang_items) == 1 and len(pusat_items) == 1
        assert cabang_items[0]["description"].startswith("[Alokasi Cabang]")
        assert pusat_items[0]["description"].startswith("[Alokasi Pusat]")
        assert abs(cabang_items[0]["total"] - 24_000_000.0) < 1.0
        assert abs(pusat_items[0]["total"] - 30_000_000.0) < 1.0

    def test_us_separates_cabang_and_pusat(self, client):
        _, _, unit = self._setup(client, "US")
        data = client.get(f"/organizations/{unit}/simulation/us").json()

        assert abs(data["cabang_allocated_us_cost"] - 120_000_000.0) < 1.0
        assert abs(data["pusat_allocated_us_cost"] - 90_000_000.0) < 1.0
        assert abs(data["total_us_cost"] - 210_000_000.0) < 1.0

        cabang_items = data["cabang_allocated_components"]
        pusat_items = data["pusat_allocated_components"]
        assert len(cabang_items) == 1 and len(pusat_items) == 1
        assert cabang_items[0]["description"].startswith("[Alokasi Cabang]")
        assert pusat_items[0]["description"].startswith("[Alokasi Pusat]")
        assert abs(cabang_items[0]["total"] - 120_000_000.0) < 1.0
        assert abs(pusat_items[0]["total"] - 90_000_000.0) < 1.0
