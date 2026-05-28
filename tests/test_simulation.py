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
        # auto_up_rate = 36_000_000 / 60 = 600_000
        assert data["auto_up_rate"] == 600_000.0
        assert data["total_up_revenue"] == 36_000_000.0

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
        assert data["final_up_rate"] == 1_000_000.0
        assert data["total_up_revenue"] == 60_000_000.0

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
