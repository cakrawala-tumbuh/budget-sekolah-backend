"""Pydantic schemas untuk IncomeEntry (pendapatan manual)."""
from datetime import datetime

from pydantic import BaseModel, field_validator


class IncomeEntryBase(BaseModel):
    income_category_id: int
    line_number: int = 1
    description: str | None = None
    basis: str | None = None
    amount: float = 0.0
    notes: str | None = None

    @field_validator("line_number")
    @classmethod
    def line_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("line_number must be >= 1")
        return v

    @field_validator("amount")
    @classmethod
    def not_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("amount must not be negative")
        return v


class IncomeEntryCreate(IncomeEntryBase):
    pass


class IncomeEntryUpdate(BaseModel):
    description: str | None = None
    basis: str | None = None
    amount: float | None = None
    notes: str | None = None


class IncomeEntryRead(IncomeEntryBase):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IncomeEntryBulkCreate(BaseModel):
    entries: list[IncomeEntryCreate]
