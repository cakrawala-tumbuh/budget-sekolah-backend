"""Pydantic schemas untuk IncomeCategory."""
from datetime import datetime

from pydantic import BaseModel, field_validator

from ..models.income_category import IncomeCalcMethod


class IncomeCategoryBase(BaseModel):
    code: str
    label: str
    calc_method: IncomeCalcMethod = IncomeCalcMethod.MANUAL
    sort_order: int = 0

    @field_validator("code")
    @classmethod
    def code_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("code must not be empty")
        return v


class IncomeCategoryCreate(IncomeCategoryBase):
    pass


class IncomeCategoryUpdate(BaseModel):
    label: str | None = None
    calc_method: IncomeCalcMethod | None = None
    sort_order: int | None = None


class IncomeCategoryRead(IncomeCategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
