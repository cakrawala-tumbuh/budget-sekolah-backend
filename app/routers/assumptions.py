from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import get_org_access
from ..database import get_db
from ..crud import assumption as crud, organization as org_crud
from ..models.organization import OrgType
from ..schemas.assumption import UnitAssumptionCreate, UnitAssumptionUpdate, UnitAssumptionRead

router = APIRouter(
    prefix="/organizations/{org_id}/assumption",
    tags=["Unit Assumptions"],
    dependencies=[Depends(get_org_access)],
)


def _get_unit_or_404(db: Session, org_id: int):
    org = org_crud.get(db, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    if org.org_type != OrgType.UNIT:
        raise HTTPException(status_code=422, detail="Student assumptions only apply to UNIT organizations")
    return org


@router.get("", response_model=UnitAssumptionRead)
def get_assumption(org_id: int, db: Session = Depends(get_db)):
    _get_unit_or_404(db, org_id)
    obj = crud.get(db, org_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Asumsi belum diisi")
    return obj


@router.put("", response_model=UnitAssumptionRead)
def upsert_assumption(org_id: int, data: UnitAssumptionCreate, db: Session = Depends(get_db)):
    _get_unit_or_404(db, org_id)
    return crud.upsert(db, org_id, data)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_assumption(org_id: int, db: Session = Depends(get_db)):
    _get_unit_or_404(db, org_id)
    if not crud.delete(db, org_id):
        raise HTTPException(status_code=404, detail="Asumsi belum diisi")
