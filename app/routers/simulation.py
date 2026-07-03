from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_org_access
from ..database import get_db
from ..crud import organization as org_crud
from ..models.organization import OrgType
from ..services import simulation as svc
from ..schemas.simulation import (
    UPSimulation, USSimulation, IncomeSimulation, ExpenseSimulation,
    AllocationSimulation, DepreciationSummary, BosIncomeSimulation,
    DirectIncomeSimulation, BudgetSummary,
)

router = APIRouter(
    prefix="/organizations/{org_id}/simulation",
    tags=["Simulation"],
    dependencies=[Depends(get_org_access)],
)


def _get_org_or_404(db: Session, org_id: int):
    org = org_crud.get(db, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.get("/up", response_model=UPSimulation, summary="UP (Enrollment Fee) component simulation")
def sim_up(org_id: int, include_parent_allocation: bool = True, db: Session = Depends(get_db)):
    org = _get_org_or_404(db, org_id)
    if org.org_type != OrgType.UNIT:
        raise HTTPException(status_code=422, detail="UP simulation is only for UNIT organizations")
    return svc.simulate_up(db, org, include_parent_allocation)


@router.get("/us", response_model=USSimulation, summary="US (Tuition Fee) component simulation")
def sim_us(org_id: int, include_parent_allocation: bool = True, db: Session = Depends(get_db)):
    org = _get_org_or_404(db, org_id)
    if org.org_type != OrgType.UNIT:
        raise HTTPException(status_code=422, detail="US simulation is only for UNIT organizations")
    return svc.simulate_us(db, org, include_parent_allocation)


@router.get("/income", response_model=IncomeSimulation, summary="Total income simulation")
def sim_income(org_id: int, include_parent_allocation: bool = True, db: Session = Depends(get_db)):
    org = _get_org_or_404(db, org_id)
    return svc.simulate_income(db, org, include_parent_allocation)


@router.get("/expenses", response_model=ExpenseSimulation, summary="Total expenses simulation")
def sim_expenses(org_id: int, include_parent_allocation: bool = True, db: Session = Depends(get_db)):
    org = _get_org_or_404(db, org_id)
    return svc.simulate_expenses(db, org, include_parent_allocation)


@router.get(
    "/allocation",
    response_model=AllocationSimulation,
    summary="Contribution allocation simulation from units/branches",
)
def sim_allocation(org_id: int, db: Session = Depends(get_db)):
    org = _get_org_or_404(db, org_id)
    if org.org_type == OrgType.UNIT:
        raise HTTPException(status_code=422, detail="Allocation simulation is only for CABANG/PUSAT organizations")
    return svc.simulate_allocation(db, org)


@router.get(
    "/depreciation",
    response_model=DepreciationSummary,
    summary="Asset depreciation summary",
)
def sim_depreciation(org_id: int, db: Session = Depends(get_db)):
    org = _get_org_or_404(db, org_id)
    return svc.simulate_depreciation(db, org)


@router.get(
    "/bos-income",
    response_model=BosIncomeSimulation,
    summary="BoS income detail breakdown by expense and investment category",
)
def sim_bos_income(org_id: int, db: Session = Depends(get_db)):
    org = _get_org_or_404(db, org_id)
    if org.org_type != OrgType.UNIT:
        raise HTTPException(status_code=422, detail="BoS income simulation is only for UNIT organizations")
    return svc.simulate_bos_income(db, org)


@router.get(
    "/direct-income",
    response_model=DirectIncomeSimulation,
    summary="Direct income mapping breakdown from expense categories",
)
def sim_direct_income(org_id: int, db: Session = Depends(get_db)):
    org = _get_org_or_404(db, org_id)
    if org.org_type != OrgType.UNIT:
        raise HTTPException(status_code=422, detail="Direct income simulation is only for UNIT organizations")
    return svc.simulate_direct_income(db, org)


@router.get("/summary", response_model=BudgetSummary, summary="Full RAB budget summary")
def sim_summary(org_id: int, include_parent_allocation: bool = True, db: Session = Depends(get_db)):
    org = _get_org_or_404(db, org_id)
    return svc.simulate_summary(db, org, include_parent_allocation)
