from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import get_org_access
from ..database import get_db
from ..crud import misc as crud, organization as org_crud
from ..models.organization import OrgType
from ..schemas.contribution import (
    ContributionRateSet, ContributionRateRead,
    ContributionAllocationCreate, ContributionAllocationRead,
)

router = APIRouter(tags=["Contributions"], dependencies=[Depends(get_org_access)])


def _get_org_or_404(db: Session, org_id: int):
    org = org_crud.get(db, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


# ── Contribution Rates ────────────────────────────────────────────────────────

@router.get(
    "/organizations/{org_id}/contribution-rates",
    response_model=ContributionRateRead,
    tags=["Contributions"],
)
def get_rates(org_id: int, db: Session = Depends(get_db)):
    _get_org_or_404(db, org_id)
    rates = crud.get_rates(db, org_id)
    return ContributionRateRead(organization_id=org_id, **rates)


@router.put(
    "/organizations/{org_id}/contribution-rates",
    response_model=ContributionRateRead,
    tags=["Contributions"],
)
def set_rates(org_id: int, data: ContributionRateSet, db: Session = Depends(get_db)):
    _get_org_or_404(db, org_id)
    rates = crud.upsert_rates(db, org_id, data)
    return ContributionRateRead(organization_id=org_id, **rates)


# ── Contribution Allocations (Cabang / Pusat) ─────────────────────────────────

@router.get(
    "/organizations/{org_id}/contribution-allocations",
    response_model=list[ContributionAllocationRead],
    tags=["Contributions"],
)
def list_allocations(org_id: int, db: Session = Depends(get_db)):
    org = _get_org_or_404(db, org_id)
    if org.org_type == OrgType.UNIT:
        raise HTTPException(status_code=422, detail="Contribution allocation only applies to CABANG/PUSAT organizations")
    allocs = crud.list_allocations(db, org_id)
    return [
        ContributionAllocationRead(
            id=a.id,
            to_organization_id=a.to_organization_id,
            from_organization_id=a.from_organization_id,
            total_students=a.total_students,
            new_students=a.new_students,
            override_pct_us=a.override_pct_us,
            override_pct_up=a.override_pct_up,
            from_organization_name=a.from_organization.name if a.from_organization else None,
        )
        for a in allocs
    ]


@router.put(
    "/organizations/{org_id}/contribution-allocations",
    response_model=ContributionAllocationRead,
    status_code=status.HTTP_200_OK,
    tags=["Contributions"],
)
def upsert_allocation(
    org_id: int, data: ContributionAllocationCreate, db: Session = Depends(get_db)
):
    org = _get_org_or_404(db, org_id)
    if org.org_type == OrgType.UNIT:
        raise HTTPException(status_code=422, detail="Contribution allocation only applies to CABANG/PUSAT organizations")
    # Verify that from_organization exists
    from_org = org_crud.get(db, data.from_organization_id)
    if from_org is None:
        raise HTTPException(status_code=404, detail="Sender organization not found")
    alloc = crud.upsert_allocation(db, org_id, data)
    return ContributionAllocationRead(
        id=alloc.id,
        to_organization_id=alloc.to_organization_id,
        from_organization_id=alloc.from_organization_id,
        total_students=alloc.total_students,
        new_students=alloc.new_students,
        override_pct_us=alloc.override_pct_us,
        override_pct_up=alloc.override_pct_up,
        from_organization_name=from_org.name,
    )


@router.delete(
    "/organizations/{org_id}/contribution-allocations/{alloc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Contributions"],
)
def delete_allocation(org_id: int, alloc_id: int, db: Session = Depends(get_db)):
    _get_org_or_404(db, org_id)
    alloc = crud.get_allocation(db, alloc_id)
    if alloc is None or alloc.to_organization_id != org_id:
        raise HTTPException(status_code=404, detail="Allocation not found")
    crud.delete_allocation(db, alloc)
