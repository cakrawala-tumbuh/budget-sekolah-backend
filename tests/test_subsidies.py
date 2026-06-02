"""
Tests untuk Subsidy — subsidi langsung dari Cabang/Pusat ke penerima.

Skenario:
  - Beban subsidi di pemberi (Cabang/Pusat) menjadi pendapatan di penerima.
  - CABANG hanya boleh memberi subsidi ke UNIT anaknya.
  - PUSAT boleh memberi subsidi ke CABANG atau UNIT mana pun.
"""
from fastapi import status


def _expense_cat_id(client, code: str) -> int:
    cats = client.get("/expense-categories").json()
    return next(c["id"] for c in cats if c["code"] == code)


def _income_cat_id(client, code: str) -> int:
    cats = client.get("/income-categories").json()
    return next(c["id"] for c in cats if c["code"] == code)


def _make_org(client, code, name, org_type, parent_id=None):
    payload = {"code": code, "name": name, "org_type": org_type}
    if parent_id is not None:
        payload["parent_id"] = parent_id
    return client.post("/organizations", json=payload).json()["id"]


class TestSubsidyCRUD:
    def test_cabang_subsidizes_child_unit(self, client):
        cabang = _make_org(client, "CBG-SUB", "Cabang Sub", "CABANG")
        unit = _make_org(client, "UNIT-SUB", "Unit Sub", "UNIT", parent_id=cabang)
        exp = _expense_cat_id(client, "5590.07")  # Subsidi ke Unit
        inc = _income_cat_id(client, _any_income_code(client))
        resp = client.post(f"/organizations/{cabang}/subsidies", json={
            "recipient_org_id": unit, "expense_category_id": exp,
            "income_category_id": inc, "amount": 50_000_000.0,
        })
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["provider_org_id"] == cabang
        assert data["recipient_org_id"] == unit
        assert data["amount"] == 50_000_000.0
        assert data["expense_category_code"] == "5590.07"
        assert data["recipient_org_name"] == "Unit Sub"

    def test_pusat_subsidizes_any_unit(self, client):
        pusat = _make_org(client, "PST-SUB", "Pusat Sub", "PUSAT")
        cabang = _make_org(client, "CBG-X", "Cabang X", "CABANG", parent_id=pusat)
        unit = _make_org(client, "UNIT-X", "Unit X", "UNIT", parent_id=cabang)
        exp = _expense_cat_id(client, "5590.07")
        inc = _income_cat_id(client, _any_income_code(client))
        # Pusat → Unit (bukan anak langsung) diperbolehkan
        resp = client.post(f"/organizations/{pusat}/subsidies", json={
            "recipient_org_id": unit, "expense_category_id": exp,
            "income_category_id": inc, "amount": 10_000_000.0,
        })
        assert resp.status_code == status.HTTP_201_CREATED
        # Pusat → Cabang juga diperbolehkan
        resp2 = client.post(f"/organizations/{pusat}/subsidies", json={
            "recipient_org_id": cabang, "expense_category_id": exp,
            "income_category_id": inc, "amount": 5_000_000.0,
        })
        assert resp2.status_code == status.HTTP_201_CREATED

    def test_cabang_cannot_subsidize_non_child(self, client):
        cabang_a = _make_org(client, "CBG-A", "Cabang A", "CABANG")
        cabang_b = _make_org(client, "CBG-B", "Cabang B", "CABANG")
        other_unit = _make_org(client, "UNIT-OTHER", "Unit Lain", "UNIT", parent_id=cabang_b)
        exp = _expense_cat_id(client, "5590.07")
        inc = _income_cat_id(client, _any_income_code(client))
        resp = client.post(f"/organizations/{cabang_a}/subsidies", json={
            "recipient_org_id": other_unit, "expense_category_id": exp,
            "income_category_id": inc, "amount": 1_000_000.0,
        })
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_unit_cannot_provide_subsidy(self, client):
        unit = _make_org(client, "UNIT-PROV-ERR", "Unit Provider", "UNIT")
        exp = _expense_cat_id(client, "5590.07")
        inc = _income_cat_id(client, _any_income_code(client))
        resp = client.post(f"/organizations/{unit}/subsidies", json={
            "recipient_org_id": unit, "expense_category_id": exp,
            "income_category_id": inc, "amount": 1.0,
        })
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_patch_and_delete(self, client):
        cabang = _make_org(client, "CBG-PD", "Cabang PD", "CABANG")
        unit = _make_org(client, "UNIT-PD", "Unit PD", "UNIT", parent_id=cabang)
        exp = _expense_cat_id(client, "5590.07")
        inc = _income_cat_id(client, _any_income_code(client))
        created = client.post(f"/organizations/{cabang}/subsidies", json={
            "recipient_org_id": unit, "expense_category_id": exp,
            "income_category_id": inc, "amount": 1_000_000.0,
        }).json()
        patched = client.patch(
            f"/organizations/{cabang}/subsidies/{created['id']}",
            json={"amount": 2_000_000.0, "is_active": False},
        )
        assert patched.status_code == status.HTTP_200_OK
        assert patched.json()["amount"] == 2_000_000.0
        assert patched.json()["is_active"] is False

        deleted = client.delete(f"/organizations/{cabang}/subsidies/{created['id']}")
        assert deleted.status_code == status.HTTP_204_NO_CONTENT
        remaining = client.get(f"/organizations/{cabang}/subsidies").json()
        assert not any(s["id"] == created["id"] for s in remaining)


class TestSubsidySimulation:
    def _setup(self, client, amount=50_000_000.0, active=True):
        cabang = _make_org(client, "CBG-SIM", "Cabang Sim", "CABANG")
        unit = _make_org(client, "UNIT-SIM", "Unit Sim", "UNIT", parent_id=cabang)
        client.put(f"/organizations/{unit}/assumption", json={
            "grade_1": 30, "grade_2": 0, "grade_3": 0, "grade_4": 0,
            "grade_5": 0, "grade_6": 0, "new_student_count": 30,
            "returning_student_count": 0, "staff_count": 3,
        })
        exp = _expense_cat_id(client, "5590.07")
        inc_code = _any_income_code(client)
        inc = _income_cat_id(client, inc_code)
        client.post(f"/organizations/{cabang}/subsidies", json={
            "recipient_org_id": unit, "expense_category_id": exp,
            "income_category_id": inc, "amount": amount, "is_active": active,
        })
        return cabang, unit, inc_code

    def test_subsidy_appears_as_income_at_recipient(self, client):
        cabang, unit, inc_code = self._setup(client, amount=50_000_000.0)
        resp = client.get(f"/organizations/{unit}/simulation/income")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        sub_items = [i for i in data["items"] if i["account_code"] == inc_code
                     and "Subsidi" in i["description"]]
        assert len(sub_items) == 1
        assert abs(sub_items[0]["total"] - 50_000_000.0) < 1.0

    def test_subsidy_appears_as_expense_at_provider(self, client):
        cabang, unit, inc_code = self._setup(client, amount=50_000_000.0)
        resp = client.get(f"/organizations/{cabang}/simulation/expenses")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        # 5590.07 non-operasional
        sub_items = [i for i in data["non_operational"] if i["account_code"] == "5590.07"]
        assert len(sub_items) == 1
        assert abs(sub_items[0]["total"] - 50_000_000.0) < 1.0

    def test_inactive_subsidy_excluded(self, client):
        cabang, unit, inc_code = self._setup(client, amount=50_000_000.0, active=False)
        income = client.get(f"/organizations/{unit}/simulation/income").json()
        assert not any("Subsidi" in i["description"] for i in income["items"])
        expenses = client.get(f"/organizations/{cabang}/simulation/expenses").json()
        assert not any(i["account_code"] == "5590.07" for i in expenses["non_operational"])


def _any_income_code(client) -> str:
    """Kembalikan satu kode kategori pendapatan yang ada untuk dipakai sebagai tujuan subsidi."""
    cats = client.get("/income-categories").json()
    return cats[0]["code"]
