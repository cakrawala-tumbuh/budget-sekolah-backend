"""Test CRUD organisasi dan endpoint /organizations."""

from fastapi import status

from app.auth import get_current_user
from app.main import app
from app.models.user import User, UserRole


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


class TestCashBalance:
    def test_default_cash_balance_zero(self, client):
        resp = _create_unit(client, code="SD-CASH-DEF")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["cash_balance"] == 0.0

    def test_create_with_cash_balance(self, client):
        resp = client.post("/organizations", json={
            "code": "SD-CASH-NEW", "name": "SD Cash", "org_type": "UNIT",
            "cash_balance": 25_000_000.0,
        })
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["cash_balance"] == 25_000_000.0

    def test_update_cash_balance(self, client):
        org = _create_unit(client, code="SD-CASH-UPD").json()
        resp = client.put(f"/organizations/{org['id']}", json={"cash_balance": 7_500_000.0})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["cash_balance"] == 7_500_000.0


class TestHierarchicalAccess:
    """Organisasi yang lebih tinggi bisa melihat semua naungannya, berjenjang."""

    def _build_tree(self, client):
        """Bangun PUSAT → CABANG → UNIT dan kembalikan id-nya."""
        pusat = client.post("/organizations", json={
            "code": "PUSAT-HX", "name": "Pusat", "org_type": "PUSAT",
        }).json()
        cabang = client.post("/organizations", json={
            "code": "CABANG-HX", "name": "Cabang", "org_type": "CABANG",
            "parent_id": pusat["id"],
        }).json()
        unit = client.post("/organizations", json={
            "code": "UNIT-HX", "name": "Unit", "org_type": "UNIT",
            "parent_id": cabang["id"],
        }).json()
        return pusat["id"], cabang["id"], unit["id"]

    def _as_org(self, org_id):
        """Override current_user menjadi user ORG dengan org_id tertentu."""
        def _override():
            return User(
                id=1000 + org_id, username=f"org{org_id}", hashed_password="",
                role=UserRole.ORG, org_id=org_id, is_active=True,
            )
        app.dependency_overrides[get_current_user] = _override

    def test_descendant_ids_cascade(self, db_session):
        from app.crud import organization as crud
        from app.schemas.organization import OrganizationCreate

        pusat = crud.create(db_session, OrganizationCreate(
            code="PUSAT-CTE", name="Pusat", org_type="PUSAT"))
        cabang = crud.create(db_session, OrganizationCreate(
            code="CABANG-CTE", name="Cabang", org_type="CABANG", parent_id=pusat.id))
        unit = crud.create(db_session, OrganizationCreate(
            code="UNIT-CTE", name="Unit", org_type="UNIT", parent_id=cabang.id))

        # PUSAT menaungi dirinya, cabang, dan unit (berjenjang sampai bawah)
        assert crud.get_descendant_ids(db_session, pusat.id) == {pusat.id, cabang.id, unit.id}
        # CABANG menaungi dirinya dan unit, bukan pusat
        assert crud.get_descendant_ids(db_session, cabang.id) == {cabang.id, unit.id}
        # UNIT hanya dirinya sendiri
        assert crud.get_descendant_ids(db_session, unit.id) == {unit.id}

    def test_pusat_can_access_descendants(self, client):
        pusat_id, cabang_id, unit_id = self._build_tree(client)
        self._as_org(pusat_id)
        # PUSAT bisa mengakses detail cabang dan unit di bawahnya
        assert client.get(f"/organizations/{cabang_id}").status_code == status.HTTP_200_OK
        assert client.get(f"/organizations/{unit_id}").status_code == status.HTTP_200_OK

    def test_unit_cannot_access_parent(self, client):
        pusat_id, cabang_id, unit_id = self._build_tree(client)
        self._as_org(unit_id)
        # UNIT tidak boleh mengakses cabang/pusat di atasnya
        assert client.get(f"/organizations/{cabang_id}").status_code == status.HTTP_403_FORBIDDEN
        assert client.get(f"/organizations/{pusat_id}").status_code == status.HTTP_403_FORBIDDEN
        # tapi boleh mengakses dirinya sendiri
        assert client.get(f"/organizations/{unit_id}").status_code == status.HTTP_200_OK

    def test_list_scoped_to_subtree(self, client):
        pusat_id, cabang_id, unit_id = self._build_tree(client)
        self._as_org(cabang_id)
        ids = {o["id"] for o in client.get("/organizations").json()}
        # CABANG melihat dirinya + unit, tidak melihat pusat
        assert cabang_id in ids and unit_id in ids
        assert pusat_id not in ids


class TestDeleteOrganization:
    def test_delete(self, client):
        org = _create_unit(client, code="SD-DEL").json()
        resp = client.delete(f"/organizations/{org['id']}")
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert client.get(f"/organizations/{org['id']}").status_code == status.HTTP_404_NOT_FOUND

    def test_delete_not_found(self, client):
        resp = client.delete("/organizations/999999")
        assert resp.status_code == status.HTTP_404_NOT_FOUND
