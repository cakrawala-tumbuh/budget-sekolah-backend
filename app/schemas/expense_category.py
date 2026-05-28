"""Pydantic schemas untuk ExpenseCategory."""
from datetime import datetime

from pydantic import BaseModel, field_validator


class ExpenseCategoryBase(BaseModel):
    code: str
    label: str
    is_operational: bool = True
    is_up_component: bool = False
    is_direct_income: bool = False
    maps_to_income_category_id: int | None = None
    contribution_role: str | None = None
    sort_order: int = 0

    @field_validator("code")
    @classmethod
    def code_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("code must not be empty")
        return v


class ExpenseCategoryCreate(ExpenseCategoryBase):
    pass


class ExpenseCategoryUpdate(BaseModel):
    label: str | None = None
    is_operational: bool | None = None
    is_up_component: bool | None = None
    is_direct_income: bool | None = None
    maps_to_income_category_id: int | None = None
    contribution_role: str | None = None
    sort_order: int | None = None


class ExpenseCategoryRead(ExpenseCategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
