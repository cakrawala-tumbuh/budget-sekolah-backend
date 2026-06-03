"""
Kontrol akses router kategori referensi (expense/income/investment).

Aturan: user organisasi (non-admin) boleh MEMBACA kategori (GET) karena ini
data referensi yang dibutuhkan untuk melihat/mengedit entri miliknya, tetapi
operasi tulis (create/update/delete/seed) tetap khusus admin.
"""
import pytest
from fastapi import status

from app.auth import get_current_user
from app.main import app
from app.models.user import User, UserRole


@pytest.fixture()
def as_org(client):
    """Override current_user menjadi user ORG (non-admin) dengan org_id=1."""
    def _override():
        return User(
            id=1001, username="org1", hashed_password="",
            role=UserRole.ORG, org_id=1, is_active=True,
        )
    app.dependency_overrides[get_current_user] = _override
    return client


CATEGORY_PREFIXES = [
    "/expense-categories",
    "/income-categories",
    "/investment-categories",
]


class TestCategoryReadAccess:
    @pytest.mark.parametrize("prefix", CATEGORY_PREFIXES)
    def test_org_user_can_list(self, as_org, prefix):
        resp = as_org.get(prefix)
        assert resp.status_code == status.HTTP_200_OK
        assert isinstance(resp.json(), list)

    @pytest.mark.parametrize("prefix", CATEGORY_PREFIXES)
    def test_org_user_can_get_one(self, as_org, prefix):
        # Ambil id pertama dari daftar (kategori sudah di-seed di conftest)
        items = as_org.get(prefix).json()
        assert items, f"Expected seeded categories for {prefix}"
        first_id = items[0]["id"]
        resp = as_org.get(f"{prefix}/{first_id}")
        assert resp.status_code == status.HTTP_200_OK


class TestCategoryWriteForbiddenForOrg:
    @pytest.mark.parametrize("prefix", CATEGORY_PREFIXES)
    def test_org_user_cannot_create(self, as_org, prefix):
        resp = as_org.post(prefix, json={"code": "9999.99", "label": "X"})
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize("prefix", CATEGORY_PREFIXES)
    def test_org_user_cannot_update(self, as_org, prefix):
        first_id = as_org.get(prefix).json()[0]["id"]
        resp = as_org.put(f"{prefix}/{first_id}", json={"label": "Diubah"})
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize("prefix", CATEGORY_PREFIXES)
    def test_org_user_cannot_delete(self, as_org, prefix):
        first_id = as_org.get(prefix).json()[0]["id"]
        resp = as_org.delete(f"{prefix}/{first_id}")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize("prefix", CATEGORY_PREFIXES)
    def test_org_user_cannot_seed(self, as_org, prefix):
        resp = as_org.post(f"{prefix}/seed-defaults")
        assert resp.status_code == status.HTTP_403_FORBIDDEN


class TestCategoryWriteAllowedForAdmin:
    @pytest.mark.parametrize("prefix", CATEGORY_PREFIXES)
    def test_admin_can_list(self, client, prefix):
        # client default berjalan sebagai admin
        assert client.get(prefix).status_code == status.HTTP_200_OK
