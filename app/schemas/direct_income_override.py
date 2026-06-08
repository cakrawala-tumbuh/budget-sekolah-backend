"""Pydantic schemas untuk DirectIncomeOverride."""
from datetime import datetime

from pydantic import BaseModel, field_validator


class DirectIncomeOverrideUpsert(BaseModel):
    override_amount: float
    notes: str | None = None

    @field_validator("override_amount")
    @classmethod
    def not_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("override_amount must not be negative")
        return v


class DirectIncomeOverrideRead(BaseModel):
    id: int
    organization_id: int
    expense_category_id: int
    override_amount: float
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
