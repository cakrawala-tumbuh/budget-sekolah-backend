"""
Pydantic schemas untuk entri anggaran biaya per kategori.

Satu ExpenseCategory dapat memiliki banyak baris rincian (line_number 1-N).
Nilai foundation = dana Yayasan, bos = dana BOS/BOP/PBOS.
BulkCreateRequest memungkinkan pengiriman sekaligus beberapa baris.
"""
from datetime import datetime

from pydantic import BaseModel, field_validator

from .grade_allocation import GradeAllocationRead


class BudgetEntryBase(BaseModel):
    expense_category_id: int
    line_number: int = 1
    description: str | None = None
    basis: str | None = None
    foundation: float = 0.0
    bos: float = 0.0
    notes: str | None = None

    @field_validator("line_number")
    @classmethod
    def line_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("line_number must be >= 1")
        return v

    @field_validator("foundation", "bos")
    @classmethod
    def not_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Budget value must not be negative")
        return v


class BudgetEntryCreate(BudgetEntryBase):
    pass


class BudgetEntryUpdate(BaseModel):
    expense_category_id: int | None = None
    description: str | None = None
    basis: str | None = None
    foundation: float | None = None
    bos: float | None = None
    notes: str | None = None


class BudgetEntryRead(BudgetEntryBase):
    id: int
    organization_id: int
    total: float
    grade_allocations: list[GradeAllocationRead] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BudgetEntryBulkCreate(BaseModel):
    entries: list[BudgetEntryCreate]
