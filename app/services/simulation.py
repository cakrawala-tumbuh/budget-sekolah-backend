"""
Simulation service — UP, US, income, expenses, and RAB summary calculations.
"""
from collections import defaultdict

from sqlalchemy.orm import Session

from ..config import settings
from ..crud import budget_entry as crud_entry, assumption as crud_assumption
from ..crud import investment as crud_inv, misc as crud_misc, income_entry as crud_income
from ..crud import parent_expense_allocation as crud_pea
from ..models.organization import Organization, OrgType
from ..models.income_category import IncomeCalcMethod
from ..schemas.simulation import (
    UPComponentItem, UPSimulation,
    USComponentItem, USSimulation,
    IncomeItem, IncomeSimulation,
    ExpenseAccountSummary, ExpenseSimulation,
    UnitAllocationDetail, AllocationSimulation,
    DepreciationItem, DepreciationSummary,
    BudgetSummary,
)


def _fiscal_year(budget_year: str) -> int:
    try:
        return int(budget_year.split("-")[0])
    except (ValueError, AttributeError):
        return 2025


def _get_parent_allocated_components(
    db: Session,
    org: Organization,
) -> tuple[list[UPComponentItem], list[USComponentItem], float, float]:
    """
    Hitung komponen UP dan US yang dialokasikan dari organisasi induk ke org ini.

    Distribusi proporsional berdasarkan ContributionAllocation:
    - UP: menggunakan new_students / total new_students semua anak
    - US: menggunakan total_students / total students semua anak
    Override proporsi menggunakan override_pct_up / override_pct_us di ContributionAllocation.

    Args:
        db: Database session.
        org: Organisasi anak (UNIT atau CABANG) yang menerima alokasi.

    Returns:
        Tuple (up_components, us_components, total_up_allocated, total_us_allocated).
    """
    if org.parent_id is None:
        return [], [], 0.0, 0.0

    # Ambil konfigurasi alokasi aktif dari parent
    parent_pea = crud_pea.list_active_by_org(db, org.parent_id)
    if not parent_pea:
        return [], [], 0.0, 0.0

    # Ambil ContributionAllocation dari semua anak ke parent (untuk proporsi)
    sibling_allocs = crud_misc.list_allocations(db, org.parent_id)
    total_students_all = sum(a.total_students for a in sibling_allocs) or 1
    total_new_all = sum(a.new_students for a in sibling_allocs) or 1

    # Cari alokasi milik org ini
    this_alloc = next(
        (a for a in sibling_allocs if a.from_organization_id == org.id),
        None,
    )
    if this_alloc is None:
        # Org ini tidak terdaftar di ContributionAllocation parent — tidak ada alokasi
        return [], [], 0.0, 0.0

    # Hitung proporsi untuk UP dan US
    pct_up = (
        this_alloc.override_pct_up
        if this_alloc.override_pct_up is not None
        else (this_alloc.new_students / total_new_all)
    )
    pct_us = (
        this_alloc.override_pct_us
        if this_alloc.override_pct_us is not None
        else (this_alloc.total_students / total_students_all)
    )

    up_components: list[UPComponentItem] = []
    us_components: list[USComponentItem] = []
    total_up = 0.0
    total_us = 0.0

    for pea in parent_pea:
        # Total biaya kategori ini di parent
        parent_entries = crud_entry.list_by_category(
            db, org.parent_id, pea.expense_category_id
        )
        parent_total = sum(
            (e.foundation or 0.0) + (e.bos or 0.0) for e in parent_entries
        )
        if parent_total == 0:
            continue

        cat = pea.expense_category
        cat_code = cat.code if cat else str(pea.expense_category_id)
        cat_label = cat.label if cat else "Biaya Induk"

        if pea.affects_up:
            allocated = pct_up * parent_total
            total_up += allocated
            up_components.append(UPComponentItem(
                account_code=f"ALLOC:{cat_code}",
                description=f"[Alokasi Induk] {cat_label}",
                total_yayasan=allocated,
                total_bos=0.0,
                total=allocated,
            ))
        else:
            allocated = pct_us * parent_total
            total_us += allocated
            us_components.append(USComponentItem(
                account_code=f"ALLOC:{cat_code}",
                description=f"[Alokasi Induk] {cat_label}",
                total_yayasan=allocated,
                total_bos=0.0,
                total=allocated,
            ))

    return up_components, us_components, total_up, total_us


def _get_parent_allocated_old_asset_dep(db: Session, org: Organization) -> float:
    """
    Hitung porsi depresiasi aset lama tahun berjalan dari organisasi induk
    (Cabang dan Pusat) yang dialokasikan ke unit ini, menambah beban UP.

    Depresiasi aset lama tahun ini di setiap ancestor (Cabang lalu Pusat)
    didistribusikan ke unit secara proporsional berdasarkan new_students —
    proporsi UP yang sama dengan alokasi biaya induk. Override per-unit
    menggunakan override_pct_up di ContributionAllocation ancestor.

    Args:
        db: Database session.
        org: Organisasi anak (UNIT) penerima alokasi.

    Returns:
        Total depresiasi aset lama induk (Cabang + Pusat) yang dialokasikan
        ke unit ini.
    """
    fiscal_year = _fiscal_year(settings.budget_year)
    total = 0.0
    ancestor = org.parent
    while ancestor is not None:
        old_assets = crud_misc.list_dep_by_org(db, ancestor.id)
        ancestor_dep = sum(a.dep_current_year(fiscal_year) for a in old_assets)
        if ancestor_dep:
            # Proporsi UP unit ini terhadap seluruh kontributor di ancestor
            sibling_allocs = crud_misc.list_allocations(db, ancestor.id)
            total_new_all = sum(a.new_students for a in sibling_allocs) or 1
            this_alloc = next(
                (a for a in sibling_allocs if a.from_organization_id == org.id),
                None,
            )
            if this_alloc is not None:
                pct_up = (
                    this_alloc.override_pct_up
                    if this_alloc.override_pct_up is not None
                    else (this_alloc.new_students / total_new_all)
                )
                total += pct_up * ancestor_dep
        ancestor = ancestor.parent
    return total


def _aggregate_entries(entries) -> dict:
    result = defaultdict(lambda: {"description": "", "total_yayasan": 0.0, "total_bos": 0.0, "category": None})
    for e in entries:
        cid = e.expense_category_id
        result[cid]["total_yayasan"] += e.foundation or 0.0
        result[cid]["total_bos"] += e.bos or 0.0
        if e.description and not result[cid]["description"]:
            result[cid]["description"] = e.description
        if result[cid]["category"] is None and e.expense_category is not None:
            result[cid]["category"] = e.expense_category
    return result


def simulate_up(db: Session, org: Organization) -> UPSimulation:
    entries = crud_entry.list_by_org(db, org.id)
    assumption = crud_assumption.get(db, org.id)
    investments = crud_inv.list_by_org(db, org.id)

    agg = _aggregate_entries(entries)
    components = []
    total_own_up_cost = 0.0

    for cid, data in sorted(agg.items()):
        cat = data["category"]
        if cat is not None and cat.is_up_component:
            total = data["total_yayasan"] + data["total_bos"]
            components.append(UPComponentItem(
                account_code=cat.code,
                description=data["description"] or cat.label,
                total_yayasan=data["total_yayasan"],
                total_bos=data["total_bos"],
                total=total,
            ))
            total_own_up_cost += total

    # Komponen UP yang dialokasikan dari organisasi induk (ditampilkan terpisah)
    allocated_up_components, _, parent_allocated_up_cost, _ = _get_parent_allocated_components(db, org)
    total_up_cost = total_own_up_cost + parent_allocated_up_cost

    new_investment_dep = sum(i.dep_current_year for i in investments)
    fiscal_year = _fiscal_year(settings.budget_year)
    old_assets = crud_misc.list_dep_by_org(db, org.id)
    old_asset_dep = sum(old.dep_current_year(fiscal_year) for old in old_assets)
    # Depresiasi aset lama tahun ini di Cabang/Pusat dialokasikan ke unit,
    # menambah beban (alokasi) UP unit.
    parent_allocated_old_asset_dep = _get_parent_allocated_old_asset_dep(db, org)
    total_dep = new_investment_dep + old_asset_dep + parent_allocated_old_asset_dep
    total_up_cost_with_dep = total_up_cost + total_dep
    new_student_count = (assumption.new_student_count if assumption else 0) or 1
    dep_per_student = total_dep / new_student_count
    auto_up_rate = total_up_cost_with_dep / new_student_count
    # Override hanya menggantikan komponen biaya (5130.xx + alokasi induk).
    # Depresiasi aset baru dan lama selalu ditambahkan ke tarif akhir,
    # sehingga perubahan data depresiasi selalu tercermin pada besaran UP.
    override = assumption.override_up_rate if assumption else None
    auto_component_rate = total_up_cost / new_student_count
    component_rate = override if override is not None else auto_component_rate
    final_up_rate = component_rate + dep_per_student
    total_up_revenue = final_up_rate * new_student_count

    return UPSimulation(
        components=components,
        allocated_components=allocated_up_components,
        total_up_cost=total_up_cost,
        parent_allocated_up_cost=parent_allocated_up_cost,
        new_investment_dep=new_investment_dep,
        old_asset_dep=old_asset_dep,
        parent_allocated_old_asset_dep=parent_allocated_old_asset_dep,
        total_up_cost_with_dep=total_up_cost_with_dep,
        new_student_count=new_student_count,
        auto_up_rate=auto_up_rate,
        final_up_rate=final_up_rate,
        total_up_revenue=total_up_revenue,
    )


def simulate_us(db: Session, org: Organization) -> USSimulation:
    entries = crud_entry.list_by_org(db, org.id)
    assumption = crud_assumption.get(db, org.id)

    agg = _aggregate_entries(entries)
    components = []
    total_own_us_cost = 0.0

    for cid, data in sorted(agg.items()):
        cat = data["category"]
        if cat is None:
            continue
        if cat.is_operational and not cat.is_up_component and not cat.is_direct_income:
            total = data["total_yayasan"] + data["total_bos"]
            components.append(USComponentItem(
                account_code=cat.code,
                description=data["description"] or cat.label,
                total_yayasan=data["total_yayasan"],
                total_bos=data["total_bos"],
                total=total,
            ))
            total_own_us_cost += total

    # Komponen US yang dialokasikan dari organisasi induk (ditampilkan terpisah)
    _, allocated_us_components, _, parent_allocated_us_cost = _get_parent_allocated_components(db, org)
    total_us_cost = total_own_us_cost + parent_allocated_us_cost

    total_students = (assumption.total_students if assumption else 0) or 1
    months = 12
    auto_us_rate = total_us_cost / (total_students * months)
    override = assumption.override_us_rate if assumption else None
    final_us_rate = override if override is not None else auto_us_rate
    total_us_revenue = final_us_rate * total_students * months

    return USSimulation(
        components=components,
        allocated_components=allocated_us_components,
        total_us_cost=total_us_cost,
        parent_allocated_us_cost=parent_allocated_us_cost,
        total_students=total_students,
        months=months,
        auto_us_rate=auto_us_rate,
        final_us_rate=final_us_rate,
        total_us_revenue=total_us_revenue,
    )


def simulate_income(db: Session, org: Organization) -> IncomeSimulation:
    """
    Hitung total pendapatan simulasi untuk suatu organisasi.

    Untuk UNIT: UP + US + direct income + BOS + manual income entries.
    Untuk CABANG/PUSAT: kontribusi UP dan US dari setiap child UNIT
      (revenue aktual unit × tarif kontribusi unit ke parent ini)
      ditambah manual income entries.

    Args:
        db: Database session.
        org: Organisasi yang disimulasikan.

    Returns:
        IncomeSimulation dengan daftar item pendapatan dan total.
    """
    items = []
    total = 0.0

    if org.org_type == OrgType.UNIT:
        up_sim = simulate_up(db, org)
        items.append(IncomeItem(account_code="4110.01", description="Uang Pangkal (UP)", total=up_sim.total_up_revenue))
        total += up_sim.total_up_revenue

        us_sim = simulate_us(db, org)
        items.append(IncomeItem(account_code="4120.01", description="Uang Sekolah (US)", total=us_sim.total_us_revenue))
        total += us_sim.total_us_revenue

        entries = crud_entry.list_by_org(db, org.id)
        agg = _aggregate_entries(entries)

        for cid, data in sorted(agg.items()):
            cat = data["category"]
            if cat is None or not cat.is_direct_income:
                continue
            amount = data["total_yayasan"] + data["total_bos"]
            if not amount:
                continue
            income_cat = cat.maps_to_income_category
            income_code = income_cat.code if income_cat else cat.code
            if income_cat and income_cat.calc_method == IncomeCalcMethod.GRADE_BASED:
                grade_total = sum(
                    ga.amount
                    for e in entries if e.expense_category_id == cid
                    for ga in e.grade_allocations
                )
                amount = grade_total if grade_total else amount
            items.append(IncomeItem(account_code=income_code, description=data["description"] or cat.label, total=amount))
            total += amount

        # SUM_FROM_BOS: jumlahkan kolom bos dari seluruh BudgetEntry
        from ..crud import income_category as crud_income_cat
        bos_categories = [
            c for c in crud_income_cat.list_all(db)
            if c.calc_method == IncomeCalcMethod.SUM_FROM_BOS
        ]
        if bos_categories:
            total_bos = sum(e.bos or 0.0 for e in entries)
            if total_bos:
                for bos_cat in bos_categories:
                    items.append(IncomeItem(account_code=bos_cat.code, description=bos_cat.label, total=total_bos))
                    total += total_bos

        income_entries = crud_income.list_by_org(db, org.id)
        income_agg = defaultdict(lambda: {"total": 0.0, "desc": "", "code": ""})
        for ie in income_entries:
            cid = ie.income_category_id
            income_agg[cid]["total"] += ie.amount or 0.0
            if not income_agg[cid]["desc"] and ie.description:
                income_agg[cid]["desc"] = ie.description
            if ie.income_category:
                income_agg[cid]["code"] = ie.income_category.code
        for cid, data in sorted(income_agg.items()):
            if data["total"]:
                items.append(IncomeItem(account_code=data["code"], description=data["desc"] or data["code"], total=data["total"]))
                total += data["total"]

    else:
        # Untuk CABANG/PUSAT: pendapatan berasal dari kontribusi UP dan US
        # setiap child UNIT, dihitung dari UP/US revenue aktual unit × tarif
        # kontribusi unit tersebut (bukan dari pengeluaran CABANG sendiri).
        allocations = crud_misc.list_allocations(db, org.id)
        up_rate_key = "up_to_cabang" if org.org_type == OrgType.CABANG else "up_to_pusat"
        us_rate_key = "us_to_cabang" if org.org_type == OrgType.CABANG else "us_to_pusat"

        for alloc in allocations:
            from_org = alloc.from_organization
            if from_org is None or from_org.org_type != OrgType.UNIT:
                continue
            unit_rates = crud_misc.get_rates(db, from_org.id)
            up_revenue = simulate_up(db, from_org).total_up_revenue
            us_revenue = simulate_us(db, from_org).total_us_revenue
            contribution_up = up_revenue * unit_rates.get(up_rate_key, 0.0)
            contribution_us = us_revenue * unit_rates.get(us_rate_key, 0.0)
            name = from_org.name
            if contribution_up:
                items.append(IncomeItem(account_code="4630.01", description=f"Kontribusi UP dari {name}", total=contribution_up))
                total += contribution_up
            if contribution_us:
                items.append(IncomeItem(account_code="4630.02", description=f"Kontribusi US dari {name}", total=contribution_us))
                total += contribution_us

        income_entries = crud_income.list_by_org(db, org.id)
        income_agg = defaultdict(lambda: {"total": 0.0, "desc": "", "code": ""})
        for ie in income_entries:
            cid = ie.income_category_id
            income_agg[cid]["total"] += ie.amount or 0.0
            if not income_agg[cid]["desc"] and ie.description:
                income_agg[cid]["desc"] = ie.description
            if ie.income_category:
                income_agg[cid]["code"] = ie.income_category.code
        for cid, data in sorted(income_agg.items()):
            if data["total"]:
                items.append(IncomeItem(account_code=data["code"], description=data["desc"] or data["code"], total=data["total"]))
                total += data["total"]

    return IncomeSimulation(items=items, total=total)


def simulate_expenses(db: Session, org: Organization) -> ExpenseSimulation:
    entries = crud_entry.list_by_org(db, org.id)
    agg = _aggregate_entries(entries)

    operational = []
    non_operational = []
    total_op = 0.0
    total_non_op = 0.0

    for cid, data in sorted(agg.items()):
        cat = data["category"]
        if cat is None:
            continue
        total = data["total_yayasan"] + data["total_bos"]
        item = ExpenseAccountSummary(
            account_code=cat.code,
            description=data["description"] or cat.label,
            total_yayasan=data["total_yayasan"],
            total_bos=data["total_bos"],
            total=total,
        )
        if cat.is_operational:
            operational.append(item)
            total_op += total
        else:
            non_operational.append(item)
            total_non_op += total

    return ExpenseSimulation(
        operational=operational,
        non_operational=non_operational,
        total_operational=total_op,
        total_non_operational=total_non_op,
        total=total_op + total_non_op,
    )


def simulate_depreciation(db: Session, org: Organization) -> DepreciationSummary:
    fiscal_year = _fiscal_year(settings.budget_year)
    investments = crud_inv.list_by_org(db, org.id)
    old_assets = crud_misc.list_dep_by_org(db, org.id)

    items = []
    total_dep = 0.0

    for inv in investments:
        dep = inv.dep_current_year
        total_dep += dep
        items.append(DepreciationItem(
            asset_code=inv.asset_code,
            asset_name=inv.asset_name,
            acquisition_cost=inv.purchase_price,
            useful_life=inv.useful_life,
            dep_per_year=inv.dep_per_year,
            current_year_dep=dep,
            book_value=inv.end_book_value,
            source="new",
        ))

    for old in old_assets:
        dep = old.dep_current_year(fiscal_year)
        total_dep += dep
        items.append(DepreciationItem(
            asset_code=old.asset_code,
            asset_name=old.asset_name,
            acquisition_cost=old.acquisition_cost,
            useful_life=old.useful_life,
            dep_per_year=old.dep_per_year(),
            current_year_dep=dep,
            book_value=old.book_value(fiscal_year),
            source="existing",
        ))

    return DepreciationSummary(items=items, total_current_year_dep=total_dep)


def simulate_allocation(db: Session, org: Organization) -> AllocationSimulation:
    """
    Hitung alokasi kontribusi UP dan US dari setiap child UNIT ke org ini.

    Kontribusi dihitung dari UP/US revenue aktual setiap unit dikalikan tarif
    kontribusi unit tersebut (up_to_cabang/up_to_pusat dan us_to_cabang/us_to_pusat).
    pct_up/pct_us menunjukkan proporsi revenue unit terhadap total pool.

    Args:
        db: Database session.
        org: Organisasi penerima kontribusi (CABANG atau PUSAT).

    Returns:
        AllocationSimulation dengan rincian kontribusi per unit.
    """
    allocations = crud_misc.list_allocations(db, org.id)
    up_rate_key = "up_to_cabang" if org.org_type == OrgType.CABANG else "up_to_pusat"
    us_rate_key = "us_to_cabang" if org.org_type == OrgType.CABANG else "us_to_pusat"

    # Pass 1: hitung revenue dan kontribusi per unit
    unit_data = []
    total_up_pool = 0.0
    total_us_pool = 0.0

    for alloc in allocations:
        from_org = alloc.from_organization
        if from_org is None or from_org.org_type != OrgType.UNIT:
            continue
        unit_rates = crud_misc.get_rates(db, from_org.id)
        up_revenue = simulate_up(db, from_org).total_up_revenue
        us_revenue = simulate_us(db, from_org).total_us_revenue
        contribution_up = up_revenue * unit_rates.get(up_rate_key, 0.0)
        contribution_us = us_revenue * unit_rates.get(us_rate_key, 0.0)
        total_up_pool += up_revenue
        total_us_pool += us_revenue
        unit_data.append({
            "alloc": alloc,
            "from_org": from_org,
            "up_revenue": up_revenue,
            "us_revenue": us_revenue,
            "contribution_up": contribution_up,
            "contribution_us": contribution_us,
        })

    # Pass 2: hitung pct dan susun hasil
    units = []
    total_k_up = 0.0
    total_k_us = 0.0

    for u in unit_data:
        alloc = u["alloc"]
        pct_up = u["up_revenue"] / total_up_pool if total_up_pool > 0 else 0.0
        pct_us = u["us_revenue"] / total_us_pool if total_us_pool > 0 else 0.0
        total_k_up += u["contribution_up"]
        total_k_us += u["contribution_us"]
        units.append(UnitAllocationDetail(
            from_organization_id=alloc.from_organization_id,
            from_organization_name=u["from_org"].name,
            total_students=alloc.total_students,
            new_students=alloc.new_students,
            pct_us=pct_us,
            pct_up=pct_up,
            contribution_us=u["contribution_us"],
            contribution_up=u["contribution_up"],
        ))

    return AllocationSimulation(
        total_base_cost_us=total_us_pool,
        total_base_cost_up=total_up_pool,
        units=units,
        total_contribution_us=total_k_us,
        total_contribution_up=total_k_up,
        is_valid=True,
    )


def simulate_summary(db: Session, org: Organization) -> BudgetSummary:
    income = simulate_income(db, org)
    expenses = simulate_expenses(db, org)
    depreciation = simulate_depreciation(db, org)
    investments = crud_inv.list_by_org(db, org.id)

    total_cash_revenue = income.total
    total_cash_expenses = expenses.total
    total_investments = sum(inv.purchase_price for inv in investments)
    cash_surplus_deficit = total_cash_revenue - total_cash_expenses - total_investments
    total_accrual_expenses = total_cash_expenses + depreciation.total_current_year_dep
    accrual_surplus_deficit = total_cash_revenue - total_accrual_expenses

    return BudgetSummary(
        organization_id=org.id,
        organization_name=org.name,
        org_type=org.org_type.value,
        budget_year=settings.budget_year,
        total_cash_revenue=total_cash_revenue,
        total_cash_expenses=total_cash_expenses,
        total_investments=total_investments,
        cash_surplus_deficit=cash_surplus_deficit,
        total_accrual_revenue=total_cash_revenue,
        total_accrual_expenses=total_accrual_expenses,
        accrual_surplus_deficit=accrual_surplus_deficit,
        income=income,
        expenses=expenses,
        depreciation=depreciation,
    )
