"""Test entri anggaran (budget entries)."""

from fastapi import status


def _expense_cat_id(client, code: str) -> int:
    cats = client.get("/expense-categories").json()
    return next(c["id"] for c in cats if c["code"] == code)


def _create_unit(client, code="SD-BE"):
    return client.post("/organizations", json={
        "code": code, "name": "SD BE Test", "org_type": "UNIT",
    }).json()["id"]


def _make_entry(cat_id: int, **overrides):
    base = {
        "expense_category_id": cat_id,
        "line_number": 1,
        "description": "Gaji 24 guru x 12 bulan",
        "basis": "24 x 12 x Rp 3.500.000",
        "foundation": 1008000000.0,
        "bos": 0.0,
    }
    base.update(overrides)
    return base


class TestBudgetEntries:
    def test_create_entry(self, client):
        org_id = _create_unit(client, code="SD-BE-1")
        cat_id = _expense_cat_id(client, "5110.01")
        resp = client.post(f"/organizations/{org_id}/budget-entries", json=_make_entry(cat_id))
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["expense_category_id"] == cat_id
        assert data["total"] == 1008000000.0

    def test_list_entries(self, client):
        org_id = _create_unit(client, code="SD-BE-2")
        cat_id = _expense_cat_id(client, "5110.01")
        client.post(f"/organizations/{org_id}/budget-entries", json=_make_entry(cat_id))
        resp = client.get(f"/organizations/{org_id}/budget-entries")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()) >= 1

    def test_filter_by_category(self, client):
        org_id = _create_unit(client, code="SD-BE-3")
        cat_5110 = _expense_cat_id(client, "5110.01")
        cat_5130 = _expense_cat_id(client, "5130.01")
        client.post(f"/organizations/{org_id}/budget-entries", json=_make_entry(cat_5110))
        client.post(f"/organizations/{org_id}/budget-entries", json=_make_entry(cat_5130, description="Pengabdian"))
        resp = client.get(f"/organizations/{org_id}/budget-entries?category_id={cat_5110}")
        assert resp.status_code == status.HTTP_200_OK
        entries = resp.json()
        assert all(e["expense_category_id"] == cat_5110 for e in entries)

    def test_update_entry(self, client):
        org_id = _create_unit(client, code="SD-BE-4")
        cat_id = _expense_cat_id(client, "5110.01")
        entry = client.post(f"/organizations/{org_id}/budget-entries", json=_make_entry(cat_id)).json()
        resp = client.put(
            f"/organizations/{org_id}/budget-entries/{entry['id']}",
            json={"foundation": 1100000000.0},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["foundation"] == 1100000000.0

    def test_delete_entry(self, client):
        org_id = _create_unit(client, code="SD-BE-5")
        cat_id = _expense_cat_id(client, "5110.01")
        entry = client.post(f"/organizations/{org_id}/budget-entries", json=_make_entry(cat_id)).json()
        resp = client.delete(f"/organizations/{org_id}/budget-entries/{entry['id']}")
        assert resp.status_code == status.HTTP_204_NO_CONTENT

    def test_negative_value_rejected(self, client):
        org_id = _create_unit(client, code="SD-BE-6")
        cat_id = _expense_cat_id(client, "5110.01")
        resp = client.post(f"/organizations/{org_id}/budget-entries", json=_make_entry(cat_id, foundation=-1))
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_bulk_create(self, client):
        org_id = _create_unit(client, code="SD-BE-7")
        cat_id = _expense_cat_id(client, "5110.01")
        payload = {"entries": [
            _make_entry(cat_id, line_number=1),
            _make_entry(cat_id, line_number=2, description="THR", foundation=84000000.0),
        ]}
        resp = client.post(f"/organizations/{org_id}/budget-entries/bulk", json=payload)
        assert resp.status_code == status.HTTP_201_CREATED
        assert len(resp.json()) == 2

    def test_delete_by_category(self, client):
        org_id = _create_unit(client, code="SD-BE-8")
        cat_id = _expense_cat_id(client, "5110.01")
        client.post(f"/organizations/{org_id}/budget-entries", json=_make_entry(cat_id))
        resp = client.delete(f"/organizations/{org_id}/budget-entries/by-category/{cat_id}")
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        entries = client.get(f"/organizations/{org_id}/budget-entries?category_id={cat_id}").json()
        assert entries == []
