"""Response schemas for RAB simulation calculations."""

from pydantic import BaseModel


# ── UP Calculation ────────────────────────────────────────────────────────────

class UPComponentItem(BaseModel):
    account_code: str
    description: str
    total_yayasan: float
    total_bos: float
    total: float


class UPSimulation(BaseModel):
    components: list[UPComponentItem]
    # Komponen biaya UP yang dialokasikan dari organisasi induk (Cabang/Pusat)
    allocated_components: list[UPComponentItem]
    total_up_cost: float
    # Total biaya UP yang dialokasikan dari organisasi induk (Cabang/Pusat)
    parent_allocated_up_cost: float
    new_investment_dep: float
    old_asset_dep: float
    # Depresiasi aset lama Cabang/Pusat yang dialokasikan ke unit (menambah UP)
    parent_allocated_old_asset_dep: float
    total_up_cost_with_dep: float
    new_student_count: int
    auto_up_rate: float
    final_up_rate: float           # override if provided
    total_up_revenue: float


# ── US Calculation ────────────────────────────────────────────────────────────

class USComponentItem(BaseModel):
    account_code: str
    description: str
    total_yayasan: float
    total_bos: float
    total: float


class USSimulation(BaseModel):
    components: list[USComponentItem]
    # Komponen biaya US yang dialokasikan dari organisasi induk (Cabang/Pusat)
    allocated_components: list[USComponentItem]
    total_us_cost: float
    # Total biaya US yang dialokasikan dari organisasi induk (Cabang/Pusat)
    parent_allocated_us_cost: float
    total_students: int
    months: int                    # always 12
    auto_us_rate: float
    final_us_rate: float
    total_us_revenue: float


# ── Income Detail ─────────────────────────────────────────────────────────────

class IncomeItem(BaseModel):
    account_code: str
    description: str
    total: float


class IncomeSimulation(BaseModel):
    items: list[IncomeItem]
    total: float


# ── Expense Detail ────────────────────────────────────────────────────────────

class ExpenseAccountSummary(BaseModel):
    account_code: str
    description: str
    total_yayasan: float
    total_bos: float
    total: float


class ExpenseSimulation(BaseModel):
    operational: list[ExpenseAccountSummary]
    non_operational: list[ExpenseAccountSummary]
    total_operational: float
    total_non_operational: float
    total: float


# ── Contribution Allocation (CABANG / PUSAT) ──────────────────────────────────

class UnitAllocationDetail(BaseModel):
    from_organization_id: int
    from_organization_name: str
    total_students: int
    new_students: int
    pct_us: float
    pct_up: float
    contribution_us: float
    contribution_up: float


class AllocationSimulation(BaseModel):
    total_base_cost_us: float
    total_base_cost_up: float
    units: list[UnitAllocationDetail]
    total_contribution_us: float
    total_contribution_up: float
    is_valid: bool                 # True if sum pct = 100%


# ── Depreciation ─────────────────────────────────────────────────────────────

class DepreciationItem(BaseModel):
    asset_code: str | None
    asset_name: str
    acquisition_cost: float
    useful_life: int
    dep_per_year: float
    current_year_dep: float
    book_value: float
    source: str                    # "new" | "existing"


class DepreciationSummary(BaseModel):
    items: list[DepreciationItem]
    total_current_year_dep: float


# ── Full Summary ──────────────────────────────────────────────────────────────

class BudgetSummary(BaseModel):
    organization_id: int
    organization_name: str
    org_type: str
    budget_year: str

    # Cash basis (budget entries + investments)
    total_cash_revenue: float
    total_cash_expenses: float      # budget entries (5xxx)
    total_investments: float        # investment purchases (1330)
    cash_surplus_deficit: float     # revenue - cash_expenses - investments

    # Accrual basis (replaces investment cost with depreciation)
    total_accrual_revenue: float
    total_accrual_expenses: float   # cash_expenses + depreciation
    accrual_surplus_deficit: float  # revenue - accrual_expenses

    # Detail
    income: IncomeSimulation
    expenses: ExpenseSimulation
    depreciation: DepreciationSummary
