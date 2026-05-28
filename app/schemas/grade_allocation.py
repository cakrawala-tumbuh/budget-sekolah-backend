"""Pydantic schemas untuk BudgetEntryGradeAllocation."""
from datetime import datetime

from pydantic import BaseModel, field_validator

VALID_GRADE_SLOTS = {"grade_1", "grade_2", "grade_3", "grade_4", "grade_5", "grade_6"}


class GradeAllocationBase(BaseModel):
    grade_slot: str
    amount: float = 0.0

    @field_validator("grade_slot")
    @classmethod
    def valid_slot(cls, v: str) -> str:
        if v not in VALID_GRADE_SLOTS:
            raise ValueError(f"grade_slot must be one of {sorted(VALID_GRADE_SLOTS)}")
        return v

    @field_validator("amount")
    @classmethod
    def not_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("amount must not be negative")
        return v


class GradeAllocationCreate(GradeAllocationBase):
    pass


class GradeAllocationUpdate(BaseModel):
    amount: float | None = None


class GradeAllocationRead(GradeAllocationBase):
    id: int
    budget_entry_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
