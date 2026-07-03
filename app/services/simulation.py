"""
Simulation service — UP, US, income, expenses, and RAB summary calculations.
"""
from collections import defaultdict
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from ..config import settings
from ..crud import budget_entry as crud_entry, assumption as crud_assumption
from ..crud import investment as crud_inv, misc as crud_misc, income_entry as crud_income
from ..crud import parent_expense_allocation as crud_pea
from ..crud import subsidy as crud_subsidy
from ..crud import direct_income_override as crud_dio
from ..crud import financial_investment as crud_fin_inv
from ..crud import organization as org_crud
from ..models.organization import Organization, OrgType
from ..models.income_category import IncomeCalcMethod
from ..schemas.simulation import (
    UPComponentItem, UPSimulation,
    USComponentItem, USSimulation,
    IncomeItem, IncomeSimulation,
    ExpenseAccountSummary, ExpenseSimulation,
    UnitAllocationDetail, AllocationSimulation,
    DepreciationItem, DepreciationSummary,
    BosIncomeLineItem, BosIncomeSimulation,
    DirectIncomeItem, DirectIncomeSimulation,
    BudgetSummary, OrgSummaryRow, ComparativeSummary,
)


def _fiscal_year(budget_year: str) -> int:
    try:
        return int(budget_year.split("-")[0])
    except (ValueError, AttributeError):
        return 2025


@dataclass
class _ParentAllocation:
    """
    Komponen biaya UP/US yang dialokasikan dari organisasi induk ke unit,
    dipisahkan berdasarkan jenis induk: Cabang vs Pusat.
    """
    up_cabang: list[UPComponentItem] = field(default_factory=list)
    up_pusat: list[UPComponentItem] = field(default_factory=list)
    us_cabang: list[USComponentItem] = field(default_factory=list)
    us_pusat: list[USComponentItem] = field(default_factory=list)
    total_up_cabang: float = 0.0
    total_up_pusat: float = 0.0
    total_us_cabang: float = 0.0
    total_us_pusat: float = 0.0


def _ancestor_pcts(
    db: Session, org: Organization, ancestor: Organization
) -> tuple[float, float] | None:
    """
    Proporsi (pct_up, pct_us) org di suatu ancestor berdasarkan
    ContributionAllocation.

    Algoritma:
    - Unit dengan ``override_pct_up``/``override_pct_us`` memakai nilai override.
    - Unit tanpa override mendapat proporsi otomatis dari sisa (1 - jumlah_semua_override)
      dibagi proporsional berdasarkan jumlah siswa unit tersebut terhadap total
      siswa seluruh unit tanpa override.
    - Jumlah seluruh proporsi final selalu tepat 100 %.

    Returns:
        Tuple (pct_up, pct_us), atau None bila org tidak terdaftar sebagai
        kontributor di ancestor.
    """
    sibling_allocs = crud_misc.list_allocations(db, ancestor.id)
    this_alloc = next(
        (a for a in sibling_allocs if a.from_organization_id == org.id),
        None,
    )
    if this_alloc is None:
        return None

    # UP — proporsi berdasarkan new_students
    if this_alloc.override_pct_up is not None:
        pct_up = this_alloc.override_pct_up
    else:
        sum_override_up = sum(
            a.override_pct_up for a in sibling_allocs if a.override_pct_up is not None
        )
        remaining_up = max(0.0, 1.0 - sum_override_up)
        auto_new_total = (
            sum(a.new_students for a in sibling_allocs if a.override_pct_up is None) or 1
        )
        pct_up = remaining_up * (this_alloc.new_students / auto_new_total)

    # US — proporsi berdasarkan total_students
    if this_alloc.override_pct_us is not None:
        pct_us = this_alloc.override_pct_us
    else:
        sum_override_us = sum(
            a.override_pct_us for a in sibling_allocs if a.override_pct_us is not None
        )
        remaining_us = max(0.0, 1.0 - sum_override_us)
        auto_students_total = (
            sum(a.total_students for a in sibling_allocs if a.override_pct_us is None) or 1
        )
        pct_us = remaining_us * (this_alloc.total_students / auto_students_total)

    return pct_up, pct_us


def _allocated_components_from_ancestor(
    db: Session,
    org: Organization,
    ancestor: Organization,
) -> tuple[list[UPComponentItem], list[USComponentItem], float, float]:
    """
    Hitung komponen UP dan US yang dialokasikan dari satu ancestor (Cabang
    atau Pusat) ke org ini, secara proporsional berdasarkan ContributionAllocation.

    - UP: proporsi dihitung via ``_ancestor_pcts`` (auto sisa override, berbasis
      new_students).
    - US: proporsi dihitung via ``_ancestor_pcts`` (auto sisa override, berbasis
      total_students).

    Returns:
        Tuple (up_components, us_components, total_up_allocated, total_us_allocated).
    """
    parent_pea = crud_pea.list_active_by_org(db, ancestor.id)
    if not parent_pea:
        return [], [], 0.0, 0.0

    pcts = _ancestor_pcts(db, org, ancestor)
    if pcts is None:
        # Org ini tidak terdaftar di ContributionAllocation ancestor — tidak ada alokasi
        return [], [], 0.0, 0.0
    pct_up, pct_us = pcts

    label_prefix = "[Alokasi Pusat]" if ancestor.org_type == OrgType.PUSAT else "[Alokasi Cabang]"

    up_components: list[UPComponentItem] = []
    us_components: list[USComponentItem] = []
    total_up = 0.0
    total_us = 0.0

    for pea in parent_pea:
        parent_entries = crud_entry.list_by_category(
            db, ancestor.id, pea.expense_category_id
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
                description=f"{label_prefix} {cat_label}",
                total_yayasan=allocated,
                total_bos=0.0,
                total=allocated,
            ))
        else:
            allocated = pct_us * parent_total
            total_us += allocated
            us_components.append(USComponentItem(
                account_code=f"ALLOC:{cat_code}",
                description=f"{label_prefix} {cat_label}",
                total_yayasan=allocated,
                total_bos=0.0,
                total=allocated,
            ))

    return up_components, us_components, total_up, total_us


def _get_parent_allocated_components(db: Session, org: Organization) -> _ParentAllocation:
    """
    Hitung komponen UP/US yang dialokasikan dari seluruh induk (Cabang lalu
    Pusat) ke org ini, dipisahkan per jenis induk.

    Menelusuri rantai induk (parent → ... → root); kontribusi tiap ancestor
    dimasukkan ke bucket Cabang atau Pusat sesuai org_type-nya.

    Args:
        db: Database session.
        org: Organisasi anak (UNIT) penerima alokasi.

    Returns:
        _ParentAllocation dengan komponen & total UP/US terpisah Cabang vs Pusat.
    """
    result = _ParentAllocation()
    ancestor = org.parent
    while ancestor is not None:
        up_c, us_c, total_up, total_us = _allocated_components_from_ancestor(db, org, ancestor)
        if ancestor.org_type == OrgType.PUSAT:
            result.up_pusat.extend(up_c)
            result.us_pusat.extend(us_c)
            result.total_up_pusat += total_up
            result.total_us_pusat += total_us
        else:  # CABANG (atau induk lain selain Pusat)
            result.up_cabang.extend(up_c)
            result.us_cabang.extend(us_c)
            result.total_up_cabang += total_up
            result.total_us_cabang += total_us
        ancestor = ancestor.parent
    return result


def _get_parent_allocated_dep(db: Session, org: Organization, ancestor_dep_fn) -> tuple[float, float]:
    """
    Hitung porsi depresiasi tahun berjalan dari organisasi induk yang
    dialokasikan ke unit ini, dipisahkan antara Cabang dan Pusat.

    Depresiasi tahun ini di tiap ancestor (dihitung oleh ``ancestor_dep_fn``)
    didistribusikan ke unit proporsional berdasarkan new_students (proporsi UP,
    override_pct_up bila ada).

    Args:
        db: Database session.
        org: Organisasi anak (UNIT) penerima alokasi.
        ancestor_dep_fn: Fungsi (ancestor) -> total depresiasi tahun ini di
            ancestor tersebut (mis. aset lama atau investasi baru).

    Returns:
        Tuple (cabang_dep, pusat_dep) — depresiasi induk yang dialokasikan ke
        unit ini dari Cabang dan dari Pusat.
    """
    cabang_dep = 0.0
    pusat_dep = 0.0
    ancestor = org.parent
    while ancestor is not None:
        ancestor_dep = ancestor_dep_fn(ancestor)
        if ancestor_dep:
            pcts = _ancestor_pcts(db, org, ancestor)
            if pcts is not None:
                pct_up, _ = pcts
                allocated = pct_up * ancestor_dep
                if ancestor.org_type == OrgType.PUSAT:
                    pusat_dep += allocated
                else:
                    cabang_dep += allocated
        ancestor = ancestor.parent
    return cabang_dep, pusat_dep


def _get_parent_allocated_old_asset_dep(db: Session, org: Organization) -> tuple[float, float]:
    """
    Porsi depresiasi aset lama tahun berjalan induk yang dialokasikan ke unit,
    dipisahkan Cabang vs Pusat. Lihat :func:`_get_parent_allocated_dep`.
    """
    fiscal_year = _fiscal_year(settings.budget_year)

    def ancestor_dep(ancestor: Organization) -> float:
        old_assets = crud_misc.list_dep_by_org(db, ancestor.id)
        return sum(a.dep_current_year(fiscal_year) for a in old_assets)

    return _get_parent_allocated_dep(db, org, ancestor_dep)


def _get_parent_allocated_new_investment_dep(db: Session, org: Organization) -> tuple[float, float]:
    """
    Porsi depresiasi investasi baru tahun berjalan induk yang dialokasikan ke
    unit, dipisahkan Cabang vs Pusat. Lihat :func:`_get_parent_allocated_dep`.
    """
    def ancestor_dep(ancestor: Organization) -> float:
        investments = crud_inv.list_by_org(db, ancestor.id)
        return sum(i.dep_current_year for i in investments)

    return _get_parent_allocated_dep(db, org, ancestor_dep)


def _get_parent_allocated_financial_investment(
    db: Session, org: Organization
) -> tuple[float, float]:
    """
    Porsi total investasi keuangan induk yang dialokasikan ke unit ini,
    dipisahkan antara Cabang dan Pusat.

    Alokasi proporsional berdasarkan pct_up (new_students) identik dengan pola
    depresiasi induk. Lihat :func:`_get_parent_allocated_dep`.
    """
    def ancestor_fin_inv(ancestor: Organization) -> float:
        return sum(fi.amount for fi in crud_fin_inv.list_by_org(db, ancestor.id))

    return _get_parent_allocated_dep(db, org, ancestor_fin_inv)


def _unit_setoran_to_ancestor(
    db: Session, org: Organization, ancestor: Organization
) -> tuple[float, float]:
    """
    Hitung setoran (kontribusi) unit ke satu ancestor (Cabang/Pusat) berbasis
    alokasi:

    - Setoran UP = beban UP induk yang dialokasikan ke unit + porsi UP unit ×
      depresiasi tahun berjalan induk (investasi baru + aset lama).
    - Setoran US = beban US induk yang dialokasikan ke unit.

    Nilai ini identik dengan beban alokasi yang ditanggung unit di
    :func:`simulate_expenses`, sehingga setoran unit (beban) = pendapatan
    kontribusi induk dan konsolidasi nyambung 1:1.

    Returns:
        Tuple (setoran_up, setoran_us). (0.0, 0.0) bila unit tidak terdaftar
        sebagai kontributor di ancestor.
    """
    pcts = _ancestor_pcts(db, org, ancestor)
    if pcts is None:
        return 0.0, 0.0
    pct_up, _ = pcts

    _, _, beban_up, beban_us = _allocated_components_from_ancestor(db, org, ancestor)

    fiscal_year = _fiscal_year(settings.budget_year)
    new_dep = sum(i.dep_current_year for i in crud_inv.list_by_org(db, ancestor.id))
    old_dep = sum(
        a.dep_current_year(fiscal_year) for a in crud_misc.list_dep_by_org(db, ancestor.id)
    )
    fin_inv_total = sum(fi.amount for fi in crud_fin_inv.list_by_org(db, ancestor.id))

    setoran_up = beban_up + pct_up * (new_dep + old_dep + fin_inv_total)
    setoran_us = beban_us
    return setoran_up, setoran_us


def _aggregate_entries(entries) -> dict:
    result = defaultdict(lambda: {"total_yayasan": 0.0, "total_bos": 0.0, "category": None})
    for e in entries:
        cid = e.expense_category_id
        result[cid]["total_yayasan"] += e.foundation or 0.0
        result[cid]["total_bos"] += e.bos or 0.0
        if result[cid]["category"] is None and e.expense_category is not None:
            result[cid]["category"] = e.expense_category
    return result


def simulate_up(
    db: Session, org: Organization, include_parent_allocation: bool = True
) -> UPSimulation:
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
                description=cat.label,
                total_yayasan=data["total_yayasan"],
                total_bos=data["total_bos"],
                total=total,
            ))
            total_own_up_cost += total

    # Komponen UP yang dialokasikan dari induk, dipisahkan Cabang vs Pusat.
    # Bila include_parent_allocation=False, simulasi murni biaya unit sendiri.
    if include_parent_allocation:
        parent_alloc = _get_parent_allocated_components(db, org)
        cabang_allocated_new_investment_dep, pusat_allocated_new_investment_dep = (
            _get_parent_allocated_new_investment_dep(db, org)
        )
        cabang_allocated_old_asset_dep, pusat_allocated_old_asset_dep = (
            _get_parent_allocated_old_asset_dep(db, org)
        )
        cabang_financial_investment_allocated, pusat_financial_investment_allocated = (
            _get_parent_allocated_financial_investment(db, org)
        )
    else:
        parent_alloc = _ParentAllocation()
        cabang_allocated_new_investment_dep = 0.0
        pusat_allocated_new_investment_dep = 0.0
        cabang_allocated_old_asset_dep = 0.0
        pusat_allocated_old_asset_dep = 0.0
        cabang_financial_investment_allocated = 0.0
        pusat_financial_investment_allocated = 0.0

    cabang_allocated_up_cost = parent_alloc.total_up_cabang
    pusat_allocated_up_cost = parent_alloc.total_up_pusat
    total_up_cost = total_own_up_cost + cabang_allocated_up_cost + pusat_allocated_up_cost

    new_investment_dep = sum(i.dep_current_year for i in investments)
    fiscal_year = _fiscal_year(settings.budget_year)
    old_assets = crud_misc.list_dep_by_org(db, org.id)
    old_asset_dep = sum(old.dep_current_year(fiscal_year) for old in old_assets)
    total_dep = (
        new_investment_dep + old_asset_dep
        + cabang_allocated_new_investment_dep + pusat_allocated_new_investment_dep
        + cabang_allocated_old_asset_dep + pusat_allocated_old_asset_dep
    )
    total_up_cost_with_dep = (
        total_up_cost + total_dep
        + cabang_financial_investment_allocated + pusat_financial_investment_allocated
    )
    new_student_count = (assumption.new_student_count if assumption else 0) or 1
    auto_up_rate = total_up_cost_with_dep / new_student_count
    # Override tarif UP diambil apa adanya dari asumsi unit sebagai tarif final
    # (tidak ditambah depresiasi atau komponen apa pun). Tanpa override, tarif
    # final = hasil kalkulasi otomatis (komponen biaya + seluruh depresiasi).
    override = assumption.override_up_rate if assumption else None
    final_up_rate = override if override is not None else auto_up_rate
    total_up_revenue = final_up_rate * new_student_count
    auto_up_revenue = auto_up_rate * new_student_count

    return UPSimulation(
        components=components,
        cabang_allocated_components=parent_alloc.up_cabang,
        pusat_allocated_components=parent_alloc.up_pusat,
        total_up_cost=total_up_cost,
        cabang_allocated_up_cost=cabang_allocated_up_cost,
        pusat_allocated_up_cost=pusat_allocated_up_cost,
        new_investment_dep=new_investment_dep,
        old_asset_dep=old_asset_dep,
        cabang_allocated_new_investment_dep=cabang_allocated_new_investment_dep,
        pusat_allocated_new_investment_dep=pusat_allocated_new_investment_dep,
        cabang_allocated_old_asset_dep=cabang_allocated_old_asset_dep,
        pusat_allocated_old_asset_dep=pusat_allocated_old_asset_dep,
        cabang_financial_investment_allocated=cabang_financial_investment_allocated,
        pusat_financial_investment_allocated=pusat_financial_investment_allocated,
        total_up_cost_with_dep=total_up_cost_with_dep,
        new_student_count=new_student_count,
        auto_up_rate=auto_up_rate,
        final_up_rate=final_up_rate,
        total_up_revenue=total_up_revenue,
        auto_up_revenue=auto_up_revenue,
    )


def simulate_us(
    db: Session, org: Organization, include_parent_allocation: bool = True
) -> USSimulation:
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
                description=cat.label,
                total_yayasan=data["total_yayasan"],
                total_bos=data["total_bos"],
                total=total,
            ))
            total_own_us_cost += total

    # Komponen US yang dialokasikan dari induk, dipisahkan Cabang vs Pusat.
    # Bila include_parent_allocation=False, simulasi murni biaya unit sendiri.
    if include_parent_allocation:
        parent_alloc = _get_parent_allocated_components(db, org)
    else:
        parent_alloc = _ParentAllocation()
    cabang_allocated_us_cost = parent_alloc.total_us_cabang
    pusat_allocated_us_cost = parent_alloc.total_us_pusat
    total_us_cost = total_own_us_cost + cabang_allocated_us_cost + pusat_allocated_us_cost

    total_students = (assumption.total_students if assumption else 0) or 1
    months = 12
    auto_us_rate = total_us_cost / (total_students * months)
    override = assumption.override_us_rate if assumption else None
    final_us_rate = override if override is not None else auto_us_rate
    total_us_revenue = final_us_rate * total_students * months
    auto_us_revenue = auto_us_rate * total_students * months

    return USSimulation(
        components=components,
        cabang_allocated_components=parent_alloc.us_cabang,
        pusat_allocated_components=parent_alloc.us_pusat,
        total_us_cost=total_us_cost,
        cabang_allocated_us_cost=cabang_allocated_us_cost,
        pusat_allocated_us_cost=pusat_allocated_us_cost,
        total_students=total_students,
        months=months,
        auto_us_rate=auto_us_rate,
        final_us_rate=final_us_rate,
        total_us_revenue=total_us_revenue,
        auto_us_revenue=auto_us_revenue,
    )


def simulate_income(
    db: Session, org: Organization, include_parent_allocation: bool = True
) -> IncomeSimulation:
    """
    Hitung total pendapatan simulasi untuk suatu organisasi.

    Untuk UNIT: UP + US + direct income + BOS + manual income entries.
    Untuk CABANG/PUSAT: kontribusi UP dan US dari setiap child UNIT
      (revenue aktual unit × tarif kontribusi unit ke parent ini)
      ditambah manual income entries.

    Args:
        db: Database session.
        org: Organisasi yang disimulasikan.
        include_parent_allocation: Sertakan beban alokasi induk (Cabang/Pusat)
            pada UP/US unit. Hanya berlaku untuk org UNIT.

    Returns:
        IncomeSimulation dengan daftar item pendapatan dan total.
    """
    items = []
    total = 0.0
    total_auto = 0.0

    if org.org_type == OrgType.UNIT:
        up_sim = simulate_up(db, org, include_parent_allocation)
        items.append(IncomeItem(
            account_code="4110.01", description="Uang Pangkal (UP)",
            total=up_sim.total_up_revenue, auto_total=up_sim.auto_up_revenue,
        ))
        total += up_sim.total_up_revenue
        total_auto += up_sim.auto_up_revenue

        us_sim = simulate_us(db, org, include_parent_allocation)
        items.append(IncomeItem(
            account_code="4120.01", description="Uang Sekolah (US)",
            total=us_sim.total_us_revenue, auto_total=us_sim.auto_us_revenue,
        ))
        total += us_sim.total_us_revenue
        total_auto += us_sim.auto_us_revenue

        entries = crud_entry.list_by_org(db, org.id)
        agg = _aggregate_entries(entries)

        overrides_map = {
            o.expense_category_id: o
            for o in crud_dio.list_by_org(db, org.id)
        }

        for cid, data in sorted(agg.items()):
            cat = data["category"]
            if cat is None or not cat.is_direct_income:
                continue
            auto_amount = data["total_yayasan"]  # BoS sudah dihitung di Pendapatan BoS
            if not auto_amount:
                continue
            income_cat = cat.maps_to_income_category
            income_code = income_cat.code if income_cat else cat.code
            if income_cat and income_cat.calc_method == IncomeCalcMethod.GRADE_BASED:
                grade_total = sum(
                    ga.amount
                    for e in entries if e.expense_category_id == cid
                    for ga in e.grade_allocations
                )
                auto_amount = grade_total if grade_total else auto_amount
            override = overrides_map.get(cid)
            final_amount = override.override_amount if override is not None else auto_amount
            items.append(IncomeItem(
                account_code=income_code,
                description=income_cat.label if income_cat else cat.label,
                total=final_amount,
                auto_total=auto_amount,
            ))
            total += final_amount
            total_auto += auto_amount

        # SUM_FROM_BOS: jumlahkan kolom bos dari seluruh BudgetEntry + Investment
        from ..crud import income_category as crud_income_cat
        bos_categories = [
            c for c in crud_income_cat.list_all(db)
            if c.calc_method == IncomeCalcMethod.SUM_FROM_BOS
        ]
        if bos_categories:
            bos_investments = crud_inv.list_by_org(db, org.id)
            total_bos = (
                sum(e.bos or 0.0 for e in entries)
                + sum(i.bos or 0.0 for i in bos_investments)
            )
            if total_bos:
                for bos_cat in bos_categories:
                    items.append(IncomeItem(account_code=bos_cat.code, description=bos_cat.label, total=total_bos, auto_total=total_bos))
                    total += total_bos
                    total_auto += total_bos

        income_entries = crud_income.list_by_org(db, org.id)
        income_agg = defaultdict(lambda: {"total": 0.0, "code": "", "label": ""})
        for ie in income_entries:
            cid = ie.income_category_id
            income_agg[cid]["total"] += ie.amount or 0.0
            if ie.income_category:
                income_agg[cid]["code"] = ie.income_category.code
                income_agg[cid]["label"] = ie.income_category.label
        for cid, data in sorted(income_agg.items()):
            if data["total"]:
                items.append(IncomeItem(account_code=data["code"], description=data["label"] or data["code"], total=data["total"], auto_total=data["total"]))
                total += data["total"]
                total_auto += data["total"]

    else:
        # Untuk CABANG/PUSAT: pendapatan berasal dari setoran (alokasi) tiap
        # child UNIT — porsi beban induk (UP+US) + depresiasi induk yang
        # ditanggung unit. Setoran ini identik dengan beban alokasi di sisi unit
        # (lihat simulate_expenses), sehingga buku unit & induk konsolidasi 1:1.
        # Tidak bergantung pada tarif UP/US unit, jadi nilai final = auto.
        allocations = crud_misc.list_allocations(db, org.id)

        for alloc in allocations:
            from_org = alloc.from_organization
            if from_org is None or from_org.org_type != OrgType.UNIT:
                continue
            setoran_up, setoran_us = _unit_setoran_to_ancestor(db, from_org, org)
            name = from_org.name
            if setoran_up:
                items.append(IncomeItem(account_code="4630.01", description=f"Kontribusi UP dari {name}", total=setoran_up, auto_total=setoran_up))
                total += setoran_up
                total_auto += setoran_up
            if setoran_us:
                items.append(IncomeItem(account_code="4630.02", description=f"Kontribusi US dari {name}", total=setoran_us, auto_total=setoran_us))
                total += setoran_us
                total_auto += setoran_us

        income_entries = crud_income.list_by_org(db, org.id)
        income_agg = defaultdict(lambda: {"total": 0.0, "code": "", "label": ""})
        for ie in income_entries:
            cid = ie.income_category_id
            income_agg[cid]["total"] += ie.amount or 0.0
            if ie.income_category:
                income_agg[cid]["code"] = ie.income_category.code
                income_agg[cid]["label"] = ie.income_category.label
        for cid, data in sorted(income_agg.items()):
            if data["total"]:
                items.append(IncomeItem(account_code=data["code"], description=data["label"] or data["code"], total=data["total"], auto_total=data["total"]))
                total += data["total"]
                total_auto += data["total"]

    # Subsidi yang DITERIMA org ini dari Cabang/Pusat menjadi pendapatan,
    # dikelompokkan per kategori pendapatan tujuan. Berlaku untuk UNIT maupun
    # CABANG penerima.
    subsidies_in = crud_subsidy.list_active_by_recipient(db, org.id)
    subsidy_income_agg = defaultdict(lambda: {"total": 0.0, "code": "", "label": ""})
    for sub in subsidies_in:
        amount = sub.amount or 0.0
        if not amount:
            continue
        key = sub.income_category_id
        subsidy_income_agg[key]["total"] += amount
        if sub.income_category:
            subsidy_income_agg[key]["code"] = sub.income_category.code
            subsidy_income_agg[key]["label"] = sub.income_category.label
    for data in subsidy_income_agg.values():
        provider_label = data["label"] or "Subsidi"
        items.append(IncomeItem(
            account_code=data["code"],
            description=f"Subsidi diterima — {provider_label}",
            total=data["total"],
            auto_total=data["total"],
        ))
        total += data["total"]
        total_auto += data["total"]

    return IncomeSimulation(items=items, total=total, total_auto=total_auto)


def simulate_expenses(
    db: Session, org: Organization, include_parent_allocation: bool = True
) -> ExpenseSimulation:
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
            description=cat.label,
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

    # Subsidi yang DIBERIKAN org ini ke penerima menjadi beban, dikelompokkan
    # per kategori biaya pemberi dan diklasifikasikan operasional/non-operasional
    # sesuai flag kategori (kategori subsidi 5590.xx bersifat non-operasional).
    subsidies_out = crud_subsidy.list_active_by_provider(db, org.id)
    subsidy_expense_agg = defaultdict(
        lambda: {"total": 0.0, "code": "", "label": "", "is_operational": False}
    )
    for sub in subsidies_out:
        amount = sub.amount or 0.0
        if not amount:
            continue
        key = sub.expense_category_id
        subsidy_expense_agg[key]["total"] += amount
        if sub.expense_category:
            subsidy_expense_agg[key]["code"] = sub.expense_category.code
            subsidy_expense_agg[key]["label"] = sub.expense_category.label
            subsidy_expense_agg[key]["is_operational"] = sub.expense_category.is_operational
    for data in subsidy_expense_agg.values():
        item = ExpenseAccountSummary(
            account_code=data["code"],
            description=f"Subsidi ke unit — {data['label'] or 'Subsidi'}",
            total_yayasan=data["total"],
            total_bos=0.0,
            total=data["total"],
        )
        if data["is_operational"]:
            operational.append(item)
            total_op += data["total"]
        else:
            non_operational.append(item)
            total_non_op += data["total"]

    # Untuk UNIT: beban yang dialokasikan dari induk (Cabang & Pusat) menjadi
    # penambah beban operasional unit:
    #   1. Seluruh beban Cabang & Pusat yang dialokasikan ke unit (UP & US).
    #   2. Depresiasi investasi baru tahun berjalan Cabang & Pusat (alokasi).
    #   3. Depresiasi aset lama tahun berjalan Cabang & Pusat (alokasi).
    # Bila include_parent_allocation=False, seluruh injeksi ini dilewati —
    # simulasi biaya murni milik unit sendiri.
    if org.org_type == OrgType.UNIT and include_parent_allocation:
        parent_alloc = _get_parent_allocated_components(db, org)
        for comp in (
            parent_alloc.up_cabang + parent_alloc.up_pusat
            + parent_alloc.us_cabang + parent_alloc.us_pusat
        ):
            operational.append(ExpenseAccountSummary(
                account_code=comp.account_code,
                description=comp.description,
                total_yayasan=comp.total,
                total_bos=0.0,
                total=comp.total,
            ))
            total_op += comp.total

        new_dep_cabang, new_dep_pusat = _get_parent_allocated_new_investment_dep(db, org)
        old_dep_cabang, old_dep_pusat = _get_parent_allocated_old_asset_dep(db, org)
        dep_lines = [
            ("ALLOC:DEP-INV-CBG", "[Alokasi Cabang] Depresiasi investasi baru", new_dep_cabang),
            ("ALLOC:DEP-INV-PST", "[Alokasi Pusat] Depresiasi investasi baru", new_dep_pusat),
            ("ALLOC:DEP-OLD-CBG", "[Alokasi Cabang] Depresiasi aset lama", old_dep_cabang),
            ("ALLOC:DEP-OLD-PST", "[Alokasi Pusat] Depresiasi aset lama", old_dep_pusat),
        ]
        for code, desc, amount in dep_lines:
            if not amount:
                continue
            operational.append(ExpenseAccountSummary(
                account_code=code,
                description=desc,
                total_yayasan=amount,
                total_bos=0.0,
                total=amount,
            ))
            total_op += amount

        # Alokasi investasi keuangan (saham/reksa dana/dll.) dari Cabang & Pusat
        fin_inv_cabang, fin_inv_pusat = _get_parent_allocated_financial_investment(db, org)
        fin_inv_lines = [
            ("ALLOC:FIN-INV-CBG", "[Alokasi Cabang] Investasi Keuangan", fin_inv_cabang),
            ("ALLOC:FIN-INV-PST", "[Alokasi Pusat] Investasi Keuangan", fin_inv_pusat),
        ]
        for code, desc, amount in fin_inv_lines:
            if not amount:
                continue
            operational.append(ExpenseAccountSummary(
                account_code=code,
                description=desc,
                total_yayasan=amount,
                total_bos=0.0,
                total=amount,
            ))
            total_op += amount

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


def _allocatable_base(db: Session, org: Organization) -> tuple[float, float]:
    """
    Total biaya induk yang dialokasikan ke unit (basis kontribusi):

    - UP: seluruh beban UP induk (PEA affects_up) + depresiasi tahun berjalan
      induk (investasi baru + aset lama).
    - US: seluruh beban US induk (PEA bukan affects_up).

    Returns:
        Tuple (base_up, base_us) — nilai 100% sebelum dibagi ke unit.
    """
    base_up = 0.0
    base_us = 0.0
    for pea in crud_pea.list_active_by_org(db, org.id):
        entries = crud_entry.list_by_category(db, org.id, pea.expense_category_id)
        total = sum((e.foundation or 0.0) + (e.bos or 0.0) for e in entries)
        if pea.affects_up:
            base_up += total
        else:
            base_us += total

    fiscal_year = _fiscal_year(settings.budget_year)
    base_up += sum(i.dep_current_year for i in crud_inv.list_by_org(db, org.id))
    base_up += sum(
        a.dep_current_year(fiscal_year) for a in crud_misc.list_dep_by_org(db, org.id)
    )
    base_up += sum(fi.amount for fi in crud_fin_inv.list_by_org(db, org.id))
    return base_up, base_us


def simulate_allocation(db: Session, org: Organization) -> AllocationSimulation:
    """
    Hitung alokasi kontribusi UP dan US dari setiap child UNIT ke org ini.

    Berbasis alokasi: setiap unit menyetor porsinya atas beban induk (UP+US)
    ditambah depresiasi tahun berjalan induk (porsi UP). pct_up/pct_us adalah
    proporsi siswa unit (new_students untuk UP, total_students untuk US) yang
    menjadi dasar pembagian. Setoran ini = beban alokasi yang ditanggung unit.

    Args:
        db: Database session.
        org: Organisasi penerima kontribusi (CABANG atau PUSAT).

    Returns:
        AllocationSimulation dengan rincian kontribusi per unit.
    """
    allocations = crud_misc.list_allocations(db, org.id)
    base_up, base_us = _allocatable_base(db, org)

    units = []
    total_k_up = 0.0
    total_k_us = 0.0

    for alloc in allocations:
        from_org = alloc.from_organization
        if from_org is None or from_org.org_type != OrgType.UNIT:
            continue
        pcts = _ancestor_pcts(db, from_org, org)
        pct_up, pct_us = pcts if pcts is not None else (0.0, 0.0)
        setoran_up, setoran_us = _unit_setoran_to_ancestor(db, from_org, org)
        total_k_up += setoran_up
        total_k_us += setoran_us
        units.append(UnitAllocationDetail(
            from_organization_id=alloc.from_organization_id,
            from_organization_name=from_org.name,
            total_students=alloc.total_students,
            new_students=alloc.new_students,
            pct_us=pct_us,
            pct_up=pct_up,
            contribution_us=setoran_us,
            contribution_up=setoran_up,
        ))

    return AllocationSimulation(
        total_base_cost_us=base_us,
        total_base_cost_up=base_up,
        units=units,
        total_contribution_us=total_k_us,
        total_contribution_up=total_k_up,
        is_valid=True,
    )


def simulate_bos_income(db: Session, org: Organization) -> BosIncomeSimulation:
    """
    Hitung detail pendapatan BoS (Bantuan Operasional Sekolah) untuk unit.

    Merangkum kolom ``bos`` dari seluruh BudgetEntry (per kategori biaya) dan
    seluruh Investment (per kategori investasi), menampilkan kontribusi BoS
    tiap komponen secara terpisah.

    Args:
        db: Database session.
        org: Organisasi UNIT yang disimulasikan.

    Returns:
        BosIncomeSimulation dengan rincian sumber BoS dan total.
    """
    entries = crud_entry.list_by_org(db, org.id)
    investments = crud_inv.list_by_org(db, org.id)

    items: list[BosIncomeLineItem] = []
    total_from_expenses = 0.0
    total_from_investments = 0.0

    # Kelompokkan entri anggaran berdasarkan kategori biaya
    exp_agg: dict = defaultdict(lambda: {"total_bos": 0.0, "category": None})
    for e in entries:
        cid = e.expense_category_id
        exp_agg[cid]["total_bos"] += e.bos or 0.0
        if exp_agg[cid]["category"] is None and e.expense_category is not None:
            exp_agg[cid]["category"] = e.expense_category

    for cid, data in sorted(exp_agg.items()):
        if not data["total_bos"]:
            continue
        cat = data["category"]
        items.append(BosIncomeLineItem(
            code=cat.code if cat else str(cid),
            description=cat.label if cat else "Biaya Operasional",
            amount=data["total_bos"],
            source="expense",
        ))
        total_from_expenses += data["total_bos"]

    # Kelompokkan investasi berdasarkan kategori investasi
    inv_agg: dict = defaultdict(lambda: {"total_bos": 0.0, "category": None})
    for inv in investments:
        cid = inv.investment_category_id
        inv_agg[cid]["total_bos"] += inv.bos or 0.0
        if inv_agg[cid]["category"] is None and inv.investment_category is not None:
            inv_agg[cid]["category"] = inv.investment_category

    for cid, data in sorted(inv_agg.items()):
        if not data["total_bos"]:
            continue
        cat = data["category"]
        items.append(BosIncomeLineItem(
            code=cat.code if cat else str(cid),
            description=cat.label if cat else "Investasi",
            amount=data["total_bos"],
            source="investment",
        ))
        total_from_investments += data["total_bos"]

    return BosIncomeSimulation(
        items=items,
        total_from_expenses=total_from_expenses,
        total_from_investments=total_from_investments,
        total=total_from_expenses + total_from_investments,
    )


def simulate_direct_income(db: Session, org: Organization) -> DirectIncomeSimulation:
    """Rincian biaya bertipe Direct Income beserta kategori pendapatan tujuannya.

    Args:
        db: Database session.
        org: Organization instance (harus UNIT).

    Returns:
        DirectIncomeSimulation berisi satu baris per expense category
        yang ber-flag is_direct_income, dengan nilai otomatis dan nilai final
        (override jika ada, otomatis jika tidak).
    """
    entries = crud_entry.list_by_org(db, org.id)
    agg = _aggregate_entries(entries)

    overrides_map = {
        o.expense_category_id: o
        for o in crud_dio.list_by_org(db, org.id)
    }

    items = []
    total = 0.0
    total_auto = 0.0

    for cid, data in sorted(agg.items()):
        cat = data["category"]
        if cat is None or not cat.is_direct_income:
            continue
        auto_amount = data["total_yayasan"]  # BoS sudah dihitung di Pendapatan BoS
        if not auto_amount:
            continue
        income_cat = cat.maps_to_income_category
        income_code = income_cat.code if income_cat else "–"
        income_label = income_cat.label if income_cat else "–"
        if income_cat and income_cat.calc_method == IncomeCalcMethod.GRADE_BASED:
            grade_total = sum(
                ga.amount
                for e in entries if e.expense_category_id == cid
                for ga in e.grade_allocations
            )
            if grade_total:
                auto_amount = grade_total
        override = overrides_map.get(cid)
        final_amount = override.override_amount if override is not None else auto_amount
        items.append(DirectIncomeItem(
            expense_category_id=cid,
            expense_code=cat.code,
            expense_label=cat.label,
            income_code=income_code,
            income_label=income_label,
            auto_total=auto_amount,
            total=final_amount,
            is_overridden=override is not None,
        ))
        total += final_amount
        total_auto += auto_amount

    return DirectIncomeSimulation(items=items, total=total, total_auto=total_auto)


def simulate_summary(
    db: Session, org: Organization, include_parent_allocation: bool = True
) -> BudgetSummary:
    income = simulate_income(db, org, include_parent_allocation)
    expenses = simulate_expenses(db, org, include_parent_allocation)
    depreciation = simulate_depreciation(db, org)
    investments = crud_inv.list_by_org(db, org.id)

    total_cash_revenue = income.total
    total_cash_revenue_auto = income.total_auto
    total_cash_expenses = expenses.total
    financial_investments = crud_fin_inv.list_by_org(db, org.id)
    total_investments = (
        sum(inv.purchase_price for inv in investments)
        + sum(fi.amount for fi in financial_investments)
    )
    cash_surplus_deficit = total_cash_revenue - total_cash_expenses - total_investments
    cash_surplus_deficit_auto = total_cash_revenue_auto - total_cash_expenses - total_investments
    # Saldo kas & setara kas: awal (dari master organisasi) + surplus/defisit kas
    opening_cash_balance = org.cash_balance or 0.0
    ending_cash_balance = opening_cash_balance + cash_surplus_deficit
    ending_cash_balance_auto = opening_cash_balance + cash_surplus_deficit_auto
    total_accrual_expenses = total_cash_expenses + depreciation.total_current_year_dep
    accrual_surplus_deficit = total_cash_revenue - total_accrual_expenses
    accrual_surplus_deficit_auto = total_cash_revenue_auto - total_accrual_expenses

    return BudgetSummary(
        organization_id=org.id,
        organization_name=org.name,
        org_type=org.org_type.value,
        budget_year=settings.budget_year,
        total_cash_revenue=total_cash_revenue,
        total_cash_revenue_auto=total_cash_revenue_auto,
        total_cash_expenses=total_cash_expenses,
        total_investments=total_investments,
        cash_surplus_deficit=cash_surplus_deficit,
        cash_surplus_deficit_auto=cash_surplus_deficit_auto,
        opening_cash_balance=opening_cash_balance,
        ending_cash_balance=ending_cash_balance,
        ending_cash_balance_auto=ending_cash_balance_auto,
        total_accrual_revenue=total_cash_revenue,
        total_accrual_revenue_auto=total_cash_revenue_auto,
        total_accrual_expenses=total_accrual_expenses,
        accrual_surplus_deficit=accrual_surplus_deficit,
        accrual_surplus_deficit_auto=accrual_surplus_deficit_auto,
        income=income,
        expenses=expenses,
        depreciation=depreciation,
    )


def simulate_comparative_summary(db: Session, org: Organization) -> ComparativeSummary:
    """
    Bangun ringkasan komparatif: organisasi (CABANG/PUSAT) vs semua UNIT di bawahnya.

    Untuk PUSAT, unit yang dibandingkan mencakup unit dari SEMUA cabang (BFS penuh
    lewat get_subtree), bukan hanya anak langsung.

    Args:
        db: Session database.
        org: Organisasi akar (harus CABANG atau PUSAT — validasi org_type di router).

    Returns:
        ComparativeSummary berisi baris organisasi itu sendiri dan baris tiap unit
        di bawahnya, masing-masing dengan dua varian summary (dengan/tanpa alokasi
        ke induk).
    """
    def _row(o: Organization) -> OrgSummaryRow:
        return OrgSummaryRow(
            parent_id=o.parent_id,
            summary_with_allocation=simulate_summary(db, o, include_parent_allocation=True),
            summary_without_allocation=simulate_summary(db, o, include_parent_allocation=False),
        )

    subtree = org_crud.get_subtree(db, org.id)
    units = [o for o in subtree if o.id != org.id and o.org_type == OrgType.UNIT]

    return ComparativeSummary(organization=_row(org), units=[_row(u) for u in units])
