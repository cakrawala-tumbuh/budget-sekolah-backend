"""Test CRUD organisasi dan endpoint /organizations."""

from fastapi import status


# ── Helpers ────────────────────────────────────────────────────────────────────

def _create_unit(client, code="SD-TEST", name="SD Test", city="Bandung"):
    return client.post("/organizations", json={
        "code": code,
        "name": name,
        "org_type": "UNIT",
        "city": city,
    })


def _create_cabang(client, code="CABANG-BDG", name="Bandung"):
    return client.post("/organizations", json={
        "code": code,
        "name": name,
        "org_type": "CABANG",
        "city": "Bandung",
    })


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestCreateOrganization:
    def test_create_unit_success(self, client):
        resp = _create_unit(client)
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["code"] == "SD-TEST"
        assert data["org_type"] == "UNIT"

    def test_duplicate_code_returns_409(self, client):
        _create_unit(client, code="SD-DUP")
        resp = _create_unit(client, code="SD-DUP")
        assert resp.status_code == status.HTTP_409_CONFLICT

    def test_code_normalized_to_uppercase(self, client):
        resp = client.post("/organizations", json={
            "code": "sd-lower",
            "name": "SD Lower",
            "org_type": "UNIT",
        })
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["code"] == "SD-LOWER"

    def test_create_with_parent(self, client):
        cabang = _create_cabang(client, code="CABANG-SMG", name="Semarang")
        parent_id = cabang.json()["id"]
        resp = client.post("/organizations", json={
            "code": "SD-SMG-01",
            "name": "SD Semarang 1",
            "org_type": "UNIT",
            "parent_id": parent_id,
        })
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["parent_id"] == parent_id


class TestReadOrganization:
    def test_list_organizations(self, client):
        _create_unit(client, code="SD-LIST-1")
        resp = client.get("/organizations")
        assert resp.status_code == status.HTTP_200_OK
        assert isinstance(resp.json(), list)

    def test_get_by_id(self, client):
        created = _create_unit(client, code="SD-GETID").json()
        resp = client.get(f"/organizations/{created['id']}")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["id"] == created["id"]

    def test_get_not_found(self, client):
        resp = client.get("/organizations/999999")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateOrganization:
    def test_update_name(self, client):
        org = _create_unit(client, code="SD-UPD").json()
        resp = client.put(f"/organizations/{org['id']}", json={"name": "SD Updated"})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["name"] == "SD Updated"


class TestDeleteOrganization:
    def test_delete(self, client):
        org = _create_unit(client, code="SD-DEL").json()
        resp = client.delete(f"/organizations/{org['id']}")
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert client.get(f"/organizations/{org['id']}").status_code == status.HTTP_404_NOT_FOUND

    def test_delete_not_found(self, client):
        resp = client.delete("/organizations/999999")
        assert resp.status_code == status.HTTP_404_NOT_FOUND
