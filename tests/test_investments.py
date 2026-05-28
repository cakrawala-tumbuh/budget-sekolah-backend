"""Tests for new fixed asset investments."""

from fastapi import status


def _invest_cat_id(client, code: str) -> int:
    cats = client.get("/investment-categories").json()
    return next(c["id"] for c in cats if c["code"] == code)


def _create_unit(client, code="SD-INV"):
    return client.post("/organizations", json={
        "code": code, "name": "SD Investasi Test", "org_type": "UNIT",
    }).json()["id"]


def _make_laptop(cat_id: int, **overrides):
    base = {
        "investment_category_id": cat_id,
        "asset_code": "LT-001",
        "asset_name": "Laptop Acer Aspire 5",
        "purchase_price": 12000000.0,
        "useful_life": 4,
        "start_month": 7,
    }
    base.update(overrides)
    return base


class TestInvestments:
    def test_create_investment(self, client):
        org_id = _create_unit(client, code="SD-INV-1")
        cat_id = _invest_cat_id(client, "1330.02")
        resp = client.post(f"/organizations/{org_id}/investments", json=_make_laptop(cat_id))
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["asset_name"] == "Laptop Acer Aspire 5"
        # dep_per_year = 12_000_000 / 4 = 3_000_000
        assert data["dep_per_year"] == 3_000_000.0
        # dep_current_year = 3_000_000 x (13-7)/12 = 1_500_000
        assert data["dep_current_year"] == 1_500_000.0

    def test_list_investments(self, client):
        org_id = _create_unit(client, code="SD-INV-2")
        cat_id = _invest_cat_id(client, "1330.02")
        client.post(f"/organizations/{org_id}/investments", json=_make_laptop(cat_id))
        resp = client.get(f"/organizations/{org_id}/investments")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()) >= 1

    def test_update_investment(self, client):
        org_id = _create_unit(client, code="SD-INV-3")
        cat_id = _invest_cat_id(client, "1330.02")
        inv = client.post(f"/organizations/{org_id}/investments", json=_make_laptop(cat_id)).json()
        resp = client.put(
            f"/organizations/{org_id}/investments/{inv['id']}",
            json={"start_month": 1},
        )
        assert resp.status_code == status.HTTP_200_OK
        # dep_current_year full year = 3_000_000
        assert resp.json()["dep_current_year"] == 3_000_000.0

    def test_delete_investment(self, client):
        org_id = _create_unit(client, code="SD-INV-4")
        cat_id = _invest_cat_id(client, "1330.02")
        inv = client.post(f"/organizations/{org_id}/investments", json=_make_laptop(cat_id)).json()
        resp = client.delete(f"/organizations/{org_id}/investments/{inv['id']}")
        assert resp.status_code == status.HTTP_204_NO_CONTENT

    def test_invalid_category_id_rejected(self, client):
        org_id = _create_unit(client, code="SD-INV-5")
        resp = client.post(
            f"/organizations/{org_id}/investments",
            json=_make_laptop(999999),  # non-existent category ID
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_invalid_bulan_rejected(self, client):
        org_id = _create_unit(client, code="SD-INV-6")
        cat_id = _invest_cat_id(client, "1330.02")
        resp = client.post(
            f"/organizations/{org_id}/investments",
            json=_make_laptop(cat_id, start_month=13),
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_dep_bulan_mulai_december(self, client):
        org_id = _create_unit(client, code="SD-INV-7")
        cat_id = _invest_cat_id(client, "1330.02")
        resp = client.post(
            f"/organizations/{org_id}/investments",
            json=_make_laptop(cat_id, start_month=12),
        )
        data = resp.json()
        # dep_per_year = 3_000_000; dep bulan 12 = 3_000_000 * 1/12 = 250_000
        assert abs(data["dep_current_year"] - 250_000.0) < 1.0
