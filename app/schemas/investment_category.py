"""Pydantic schemas untuk InvestmentCategory."""
from datetime import datetime

from pydantic import BaseModel, field_validator


class InvestmentCategoryBase(BaseModel):
    code: str
    label: str
    default_economic_life: int = 4
    sort_order: int = 0

    @field_validator("code")
    @classmethod
    def code_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("code must not be empty")
        return v

    @field_validator("default_economic_life")
    @classmethod
    def life_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("default_economic_life must be >= 1")
        return v


class InvestmentCategoryCreate(InvestmentCategoryBase):
    pass


class InvestmentCategoryUpdate(BaseModel):
    label: str | None = None
    default_economic_life: int | None = None
    sort_order: int | None = None


class InvestmentCategoryRead(InvestmentCategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
