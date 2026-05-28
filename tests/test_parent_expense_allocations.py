"""
Tests untuk ParentExpenseAllocation — alokasi biaya dari Cabang/Pusat ke Unit.

Skenario:
  - Cabang memiliki biaya salary (5110.01) yang dialokasikan sebagai beban US ke unit
  - Cabang memiliki biaya HR dev (5130.01) yang dialokasikan sebagai beban UP ke unit
  - Unit mendapat porsi proporsional sesuai jumlah siswa di ContributionAllocation
"""
from fastapi import status


def _expense_cat_id(client, code: str) -> int:
    cats = client.get("/expense-categories").json()
    return next(c["id"] for c in cats if c["code"] == code)


def _setup_cabang(client):
    """Buat Cabang dengan biaya salary 5110.01 dan dev 5130.01."""
    cabang = client.post("/organizations", json={
        "code": "CBG-PEA", "name": "Cabang PEA Test", "org_type": "CABANG",
    }).json()
    cabang_id = cabang["id"]

    cat_gaji = _expense_cat_id(client, "5110.01")
    cat_dev = _expense_cat_id(client, "5130.01")

    # Salary di Cabang: 120_000_000 → akan dialokasikan sebagai US
    client.post(f"/organizations/{cabang_id}/budget-entries", json={
        "expense_category_id": cat_gaji, "line_number": 1,
        "description": "Gaji Cabang", "foundation": 120_000_000.0, "bos": 0.0,
    })
    # HR Dev di Cabang: 24_000_000 → akan dialokasikan sebagai UP
    client.post(f"/organizations/{cabang_id}/budget-entries", json={
        "expense_category_id": cat_dev, "line_number": 1,
        "description": "Dev SDM Cabang", "foundation": 24_000_000.0, "bos": 0.0,
    })
    return cabang_id, cat_gaji, cat_dev


def _setup_unit(client, code: str, cabang_id: int, new_students: int, total_students: int):
    """Buat Unit anak dari Cabang dengan asumsi siswa."""
    org = client.post("/organizations", json={
        "code": code,
        "name": f"Unit {code}",
        "org_type": "UNIT",
        "parent_id": cabang_id,
    }).json()
    org_id = org["id"]

    client.put(f"/organizations/{org_id}/assumption", json={
        "grade_1": new_students, "grade_2": total_students - new_students,
        "grade_3": 0, "grade_4": 0, "grade_5": 0, "grade_6": 0,
        "new_student_count": new_students,
        "returning_student_count": total_students - new_students,
        "staff_count": 5,
    })
    # Daftarkan unit ke ContributionAllocation di Cabang
    client.put(f"/organizations/{cabang_id}/contribution-allocations", json={
        "from_organization_id": org_id,
        "total_students": total_students,
        "new_students": new_students,
    })
    return org_id


class TestParentExpenseAllocationCRUD:
    def test_create_on_cabang(self, client):
        cabang_id, cat_gaji, cat_dev = _setup_cabang(client)
        resp = client.post(
            f"/organizations/{cabang_id}/parent-expense-allocations",
            json={"expense_category_id": cat_gaji, "affects_up": False, "is_active": True},
        )
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["parent_org_id"] == cabang_id
        assert data["expense_category_id"] == cat_gaji
        assert data["affects_up"] is False
        assert data["expense_category_code"] == "5110.01"

    def test_duplicate_raises_409(self, client):
        cabang_id, cat_gaji, _ = _setup_cabang(client)
        client.post(
            f"/organizations/{cabang_id}/parent-expense-allocations",
            json={"expense_category_id": cat_gaji, "affects_up": False},
        )
        resp = client.post(
            f"/organizations/{cabang_id}/parent-expense-allocations",
            json={"expense_category_id": cat_gaji, "affects_up": False},
        )
        assert resp.status_code == status.HTTP_409_CONFLICT

    def test_unit_cannot_create(self, client):
        unit = client.post("/organizations", json={
            "code": "UNIT-PEA-ERR", "name": "Unit Error", "org_type": "UNIT",
        }).json()
        cat_gaji = _expense_cat_id(client, "5110.01")
        resp = client.post(
            f"/organizations/{unit['id']}/parent-expense-allocations",
            json={"expense_category_id": cat_gaji, "affects_up": False},
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_allocations(self, client):
        cabang_id, cat_gaji, cat_dev = _setup_cabang(client)
        client.post(f"/organizations/{cabang_id}/parent-expense-allocations",
                    json={"expense_category_id": cat_gaji, "affects_up": False})
        client.post(f"/organizations/{cabang_id}/parent-expense-allocations",
                    json={"expense_category_id": cat_dev, "affects_up": True})
        resp = client.get(f"/organizations/{cabang_id}/parent-expense-allocations")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()) == 2

    def test_patch_updates_fields(self, client):
        cabang_id, cat_gaji, _ = _setup_cabang(client)
        created = client.post(
            f"/organizations/{cabang_id}/parent-expense-allocations",
            json={"expense_category_id": cat_gaji, "affects_up": False, "is_active": True},
        ).json()
        resp = client.patch(
            f"/organizations/{cabang_id}/parent-expense-allocations/{created['id']}",
            json={"is_active": False},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["is_active"] is False

    def test_delete(self, client):
        cabang_id, cat_gaji, _ = _setup_cabang(client)
        created = client.post(
            f"/organizations/{cabang_id}/parent-expense-allocations",
            json={"expense_category_id": cat_gaji, "affects_up": False},
        ).json()
        resp = client.delete(
            f"/organizations/{cabang_id}/parent-expense-allocations/{created['id']}"
        )
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        # Pastikan sudah dihapus
        all_allocs = client.get(f"/organizations/{cabang_id}/parent-expense-allocations").json()
        assert not any(a["id"] == created["id"] for a in all_allocs)


class TestParentExpenseAllocationSimulation:
    def _setup_scenario(self, client):
        """
        Cabang: salary 120_000_000 (US), dev 24_000_000 (UP)
        Unit A: 60 siswa baru, 200 total
        Unit B: 40 siswa baru, 100 total
        Total new: 100, total: 300
        """
        cabang_id, cat_gaji, cat_dev = _setup_cabang(client)
        unit_a = _setup_unit(client, "UNIT-PEA-A", cabang_id, new_students=60, total_students=200)
        unit_b = _setup_unit(client, "UNIT-PEA-B", cabang_id, new_students=40, total_students=100)
        return cabang_id, unit_a, unit_b, cat_gaji, cat_dev

    def test_up_without_allocation(self, client):
        """Tanpa ParentExpenseAllocation, UP tidak terpengaruh."""
        cabang_id, unit_a, unit_b, cat_gaji, cat_dev = self._setup_scenario(client)
        resp = client.get(f"/organizations/{unit_a}/simulation/up")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["parent_allocated_up_cost"] == 0.0
        # Tidak ada biaya UP di unit itu sendiri
        assert data["total_up_cost"] == 0.0

    def test_up_with_parent_allocation(self, client):
        """
        Cabang allocates dev (5130.01) = 24_000_000 as UP.
        Unit A new_students=60, total_new=100 → pct_up = 60/100 = 0.6
        Expected UP allocated for A = 0.6 * 24_000_000 = 14_400_000
        """
        cabang_id, unit_a, unit_b, cat_gaji, cat_dev = self._setup_scenario(client)
        client.post(f"/organizations/{cabang_id}/parent-expense-allocations",
                    json={"expense_category_id": cat_dev, "affects_up": True})

        resp = client.get(f"/organizations/{unit_a}/simulation/up")
        data = resp.json()
        assert resp.status_code == status.HTTP_200_OK
        assert abs(data["parent_allocated_up_cost"] - 14_400_000.0) < 1.0
        assert abs(data["total_up_cost"] - 14_400_000.0) < 1.0

        # Pastikan komponen [Alokasi Induk] ada di list
        alloc_items = [c for c in data["components"] if c["account_code"].startswith("ALLOC:")]
        assert len(alloc_items) == 1
        assert abs(alloc_items[0]["total"] - 14_400_000.0) < 1.0

    def test_up_with_parent_allocation_unit_b(self, client):
        """
        Unit B new_students=40, total_new=100 → pct_up = 40/100 = 0.4
        Expected UP allocated for B = 0.4 * 24_000_000 = 9_600_000
        """
        cabang_id, unit_a, unit_b, cat_gaji, cat_dev = self._setup_scenario(client)
        client.post(f"/organizations/{cabang_id}/parent-expense-allocations",
                    json={"expense_category_id": cat_dev, "affects_up": True})

        resp = client.get(f"/organizations/{unit_b}/simulation/up")
        data = resp.json()
        assert abs(data["parent_allocated_up_cost"] - 9_600_000.0) < 1.0

    def test_us_with_parent_allocation(self, client):
        """
        Cabang allocates salary (5110.01) = 120_000_000 as US.
        Unit A total_students=200, total=300 → pct_us = 200/300 ≈ 0.6667
        Expected US allocated for A ≈ 0.6667 * 120_000_000 = 80_000_000
        """
        cabang_id, unit_a, unit_b, cat_gaji, cat_dev = self._setup_scenario(client)
        client.post(f"/organizations/{cabang_id}/parent-expense-allocations",
                    json={"expense_category_id": cat_gaji, "affects_up": False})

        resp = client.get(f"/organizations/{unit_a}/simulation/us")
        data = resp.json()
        assert resp.status_code == status.HTTP_200_OK
        expected_us = (200 / 300) * 120_000_000.0
        assert abs(data["parent_allocated_us_cost"] - expected_us) < 1.0
        assert abs(data["total_us_cost"] - expected_us) < 1.0

        alloc_items = [c for c in data["components"] if c["account_code"].startswith("ALLOC:")]
        assert len(alloc_items) == 1

    def test_inactive_allocation_not_included(self, client):
        """Alokasi yang is_active=False tidak dihitung dalam simulasi."""
        cabang_id, unit_a, unit_b, cat_gaji, cat_dev = self._setup_scenario(client)
        created = client.post(
            f"/organizations/{cabang_id}/parent-expense-allocations",
            json={"expense_category_id": cat_gaji, "affects_up": False, "is_active": False},
        ).json()

        resp = client.get(f"/organizations/{unit_a}/simulation/us")
        data = resp.json()
        assert data["parent_allocated_us_cost"] == 0.0

    def test_unit_without_contribution_alloc_gets_zero(self, client):
        """Unit yang tidak terdaftar di ContributionAllocation tidak mendapat alokasi."""
        cabang_id, cat_gaji, cat_dev = _setup_cabang(client)
        # Buat unit tanpa daftarkan ke contribution-allocations
        unit_no_alloc = client.post("/organizations", json={
            "code": "UNIT-NO-ALLOC", "name": "Unit Tanpa Alloc",
            "org_type": "UNIT", "parent_id": cabang_id,
        }).json()["id"]
        client.put(f"/organizations/{unit_no_alloc}/assumption", json={
            "grade_1": 30, "grade_2": 0, "grade_3": 0,
            "grade_4": 0, "grade_5": 0, "grade_6": 0,
            "new_student_count": 30, "returning_student_count": 0, "staff_count": 3,
        })
        client.post(f"/organizations/{cabang_id}/parent-expense-allocations",
                    json={"expense_category_id": cat_gaji, "affects_up": False})

        resp = client.get(f"/organizations/{unit_no_alloc}/simulation/us")
        data = resp.json()
        assert data["parent_allocated_us_cost"] == 0.0


class TestSimulateAllocationFixed:
    """Pastikan simulate_allocation tidak error setelah perbaikan field name."""
    def test_allocation_simulation_works(self, client):
        cabang = client.post("/organizations", json={
            "code": "CBG-ALLOC-FIX", "name": "Cabang Alloc Fix", "org_type": "CABANG",
        }).json()
        cabang_id = cabang["id"]
        unit = client.post("/organizations", json={
            "code": "UNIT-ALLOC-FIX", "name": "Unit Alloc Fix", "org_type": "UNIT",
            "parent_id": cabang_id,
        }).json()
        client.put(f"/organizations/{cabang_id}/contribution-allocations", json={
            "from_organization_id": unit["id"],
            "total_students": 100,
            "new_students": 40,
        })
        resp = client.get(f"/organizations/{cabang_id}/simulation/allocation")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "total_base_cost_us" in data
        assert "units" in data
        assert data["units"][0]["total_students"] == 100
        assert data["units"][0]["new_students"] == 40
