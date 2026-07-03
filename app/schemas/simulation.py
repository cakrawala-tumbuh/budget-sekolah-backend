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
    # Komponen biaya UP yang dialokasikan dari induk, dipisahkan Cabang vs Pusat
    cabang_allocated_components: list[UPComponentItem]
    pusat_allocated_components: list[UPComponentItem]
    total_up_cost: float
    # Total biaya UP yang dialokasikan dari Cabang dan dari Pusat (terpisah)
    cabang_allocated_up_cost: float
    pusat_allocated_up_cost: float
    new_investment_dep: float
    old_asset_dep: float
    # Depresiasi investasi baru tahun berjalan induk yang dialokasikan ke unit
    # (menambah UP), dipisahkan antara Cabang dan Pusat
    cabang_allocated_new_investment_dep: float
    pusat_allocated_new_investment_dep: float
    # Depresiasi aset lama induk yang dialokasikan ke unit (menambah UP),
    # dipisahkan antara Cabang dan Pusat
    cabang_allocated_old_asset_dep: float
    pusat_allocated_old_asset_dep: float
    # Investasi keuangan (saham/reksa dana/dll.) Cabang & Pusat yang dialokasikan
    # ke unit ini berdasarkan pct_up (new_students), menambah beban UP unit
    cabang_financial_investment_allocated: float
    pusat_financial_investment_allocated: float
    total_up_cost_with_dep: float
    new_student_count: int
    auto_up_rate: float
    final_up_rate: float           # override if provided
    total_up_revenue: float        # final (override) revenue
    auto_up_revenue: float         # revenue using auto rate (ignores override)


# ── US Calculation ────────────────────────────────────────────────────────────

class USComponentItem(BaseModel):
    account_code: str
    description: str
    total_yayasan: float
    total_bos: float
    total: float


class USSimulation(BaseModel):
    components: list[USComponentItem]
    # Komponen biaya US yang dialokasikan dari induk, dipisahkan Cabang vs Pusat
    cabang_allocated_components: list[USComponentItem]
    pusat_allocated_components: list[USComponentItem]
    total_us_cost: float
    # Total biaya US yang dialokasikan dari Cabang dan dari Pusat (terpisah)
    cabang_allocated_us_cost: float
    pusat_allocated_us_cost: float
    total_students: int
    months: int                    # always 12
    auto_us_rate: float
    final_us_rate: float
    total_us_revenue: float        # final (override) revenue
    auto_us_revenue: float         # revenue using auto rate (ignores override)


# ── Income Detail ─────────────────────────────────────────────────────────────

class IncomeItem(BaseModel):
    account_code: str
    description: str
    total: float                   # final (override) amount
    auto_total: float              # amount using auto-calculated UP/US (ignores override)


class IncomeSimulation(BaseModel):
    items: list[IncomeItem]
    total: float                   # final (override) total
    total_auto: float              # total using auto-calculated UP/US (ignores override)


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


# ── BoS Income Detail ─────────────────────────────────────────────────────────

class BosIncomeLineItem(BaseModel):
    code: str
    description: str
    amount: float
    source: str                     # "expense" | "investment"


class BosIncomeSimulation(BaseModel):
    items: list[BosIncomeLineItem]
    total_from_expenses: float
    total_from_investments: float
    total: float


# ── Direct Income Mapping ─────────────────────────────────────────────────────

class DirectIncomeItem(BaseModel):
    expense_category_id: int
    expense_code: str
    expense_label: str
    income_code: str
    income_label: str
    auto_total: float      # nilai otomatis dari budget entry
    total: float           # final: override jika ada, else auto_total
    is_overridden: bool


class DirectIncomeSimulation(BaseModel):
    items: list[DirectIncomeItem]
    total: float
    total_auto: float


# ── Full Summary ──────────────────────────────────────────────────────────────

class BudgetSummary(BaseModel):
    organization_id: int
    organization_name: str
    org_type: str
    budget_year: str

    # Cash basis (budget entries + investments)
    total_cash_revenue: float       # final (override) revenue
    total_cash_revenue_auto: float  # revenue using auto-calculated UP/US
    total_cash_expenses: float      # budget entries (5xxx)
    total_investments: float        # investment purchases (1330)
    cash_surplus_deficit: float     # revenue - cash_expenses - investments
    cash_surplus_deficit_auto: float  # auto revenue - cash_expenses - investments

    # Cash & cash equivalents position
    opening_cash_balance: float     # saldo kas & setara kas awal (org.cash_balance)
    ending_cash_balance: float      # opening + cash_surplus_deficit (budget kas)
    ending_cash_balance_auto: float  # opening + cash_surplus_deficit_auto

    # Accrual basis (replaces investment cost with depreciation)
    total_accrual_revenue: float
    total_accrual_revenue_auto: float
    total_accrual_expenses: float   # cash_expenses + depreciation
    accrual_surplus_deficit: float  # revenue - accrual_expenses
    accrual_surplus_deficit_auto: float  # auto revenue - accrual_expenses

    # Detail
    income: IncomeSimulation
    expenses: ExpenseSimulation
    depreciation: DepreciationSummary


# ── Comparative Summary (Cabang/Pusat vs semua unit di bawahnya) ──────────────

class OrgSummaryRow(BaseModel):
    """Satu baris ringkasan untuk satu organisasi (induk atau unit turunan)."""
    parent_id: int | None
    summary_with_allocation: BudgetSummary
    summary_without_allocation: BudgetSummary


class ComparativeSummary(BaseModel):
    """Ringkasan komparatif: organisasi induk (CABANG/PUSAT) vs seluruh unit di bawahnya."""
    organization: OrgSummaryRow
    units: list[OrgSummaryRow]
