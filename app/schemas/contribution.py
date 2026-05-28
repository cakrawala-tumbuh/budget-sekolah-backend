"""
Pydantic schemas untuk tarif kontribusi dan alokasi kontribusi.

ContributionRateSet digunakan untuk set semua tarif sekaligus (nilai 0.0–1.0).
ContributionAllocationCreate mendaftarkan alokasi dari unit/cabang ke induknya.
Semua rate divalidasi dalam rentang 0.0–1.0.
"""
from pydantic import BaseModel, field_validator

from ..models.contribution_rate import DEFAULT_RATES


class ContributionRateSet(BaseModel):
    """Payload to set all contribution rates at once."""

    up_to_pusat: float = DEFAULT_RATES["up_to_pusat"]
    up_to_cabang: float = DEFAULT_RATES["up_to_cabang"]
    us_to_pusat: float = DEFAULT_RATES["us_to_pusat"]
    us_to_cabang: float = DEFAULT_RATES["us_to_cabang"]
    development_fund: float = DEFAULT_RATES["development_fund"]
    deficit_reserve: float = DEFAULT_RATES["deficit_reserve"]
    social_care: float = DEFAULT_RATES["social_care"]
    teacher_study: float = DEFAULT_RATES["teacher_study"]

    @field_validator(
        "up_to_pusat", "up_to_cabang", "us_to_pusat", "us_to_cabang",
        "development_fund", "deficit_reserve", "social_care", "teacher_study",
    )
    @classmethod
    def rate_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("Rate must be between 0.0 and 1.0")
        return v


class ContributionRateRead(ContributionRateSet):
    organization_id: int

    model_config = {"from_attributes": True}


# ── Contribution allocation (CABANG / PUSAT) ─────────────────────────────────────

class ContributionAllocationBase(BaseModel):
    from_organization_id: int
    total_students: int = 0
    new_students: int = 0
    override_pct_us: float | None = None
    override_pct_up: float | None = None

    @field_validator("override_pct_us", "override_pct_up")
    @classmethod
    def pct_range(cls, v: float | None) -> float | None:
        if v is not None and not 0.0 <= v <= 1.0:
            raise ValueError("Override percentage must be between 0.0 and 1.0")
        return v


class ContributionAllocationCreate(ContributionAllocationBase):
    pass


class ContributionAllocationUpdate(BaseModel):
    total_students: int | None = None
    new_students: int | None = None
    override_pct_us: float | None = None
    override_pct_up: float | None = None


class ContributionAllocationRead(ContributionAllocationBase):
    id: int
    to_organization_id: int
    from_organization_name: str | None = None

    model_config = {"from_attributes": True}
