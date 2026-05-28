"""Tests for unit school student assumptions."""

from fastapi import status


def _create_unit(client, code="SD-ASM"):
    resp = client.post("/organizations", json={
        "code": code, "name": "SD Asumsi Test", "org_type": "UNIT",
    })
    return resp.json()["id"]


def _create_cabang(client, code="CBG-ASM"):
    resp = client.post("/organizations", json={
        "code": code, "name": "Cabang Asumsi Test", "org_type": "CABANG",
    })
    return resp.json()["id"]


_ASSUMPTION_PAYLOAD = {
    "grade_1": 60, "grade_2": 58, "grade_3": 55,
    "grade_4": 52, "grade_5": 50, "grade_6": 51,
    "new_student_count": 60, "returning_student_count": 266,
    "staff_count": 24,
}


class TestAssumption:
    def test_upsert_and_get(self, client):
        org_id = _create_unit(client, code="SD-ASM-1")
        resp = client.put(f"/organizations/{org_id}/assumption", json=_ASSUMPTION_PAYLOAD)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["grade_1"] == 60
        assert data["total_students"] == 326  # 60+58+55+52+50+51

    def test_get_assumption(self, client):
        org_id = _create_unit(client, code="SD-ASM-2")
        client.put(f"/organizations/{org_id}/assumption", json=_ASSUMPTION_PAYLOAD)
        resp = client.get(f"/organizations/{org_id}/assumption")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["new_student_count"] == 60

    def test_get_not_found(self, client):
        org_id = _create_unit(client, code="SD-ASM-3")
        resp = client.get(f"/organizations/{org_id}/assumption")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_assumption_only_for_unit(self, client):
        org_id = _create_cabang(client, code="CBG-ASM-1")
        resp = client.put(f"/organizations/{org_id}/assumption", json=_ASSUMPTION_PAYLOAD)
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_negative_count_rejected(self, client):
        org_id = _create_unit(client, code="SD-ASM-4")
        payload = {**_ASSUMPTION_PAYLOAD, "grade_1": -1}
        resp = client.put(f"/organizations/{org_id}/assumption", json=payload)
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_override_tarif_up(self, client):
        org_id = _create_unit(client, code="SD-ASM-5")
        payload = {**_ASSUMPTION_PAYLOAD, "override_up_rate": 5000000.0}
        resp = client.put(f"/organizations/{org_id}/assumption", json=payload)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["override_up_rate"] == 5000000.0

    def test_delete_assumption(self, client):
        org_id = _create_unit(client, code="SD-ASM-6")
        client.put(f"/organizations/{org_id}/assumption", json=_ASSUMPTION_PAYLOAD)
        resp = client.delete(f"/organizations/{org_id}/assumption")
        assert resp.status_code == status.HTTP_204_NO_CONTENT
