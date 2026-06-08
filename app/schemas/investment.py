"""
Pydantic schemas untuk pembelian aset tetap baru (Investasi).

Kategori aset ditentukan via investment_category_id (FK ke InvestmentCategory).
Depresiasi proporsional dihitung di model Investment berdasarkan
purchase_price, useful_life, dan start_month.
"""
from datetime import datetime

from pydantic import BaseModel, field_validator


class InvestmentBase(BaseModel):
    investment_category_id: int
    asset_code: str | None = None
    asset_name: str
    purchase_price: float
    bos: float = 0.0
    useful_life: int
    start_month: int

    @field_validator("purchase_price")
    @classmethod
    def positive_value(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("purchase_price must be > 0")
        return v

    @field_validator("useful_life")
    @classmethod
    def positive_life(cls, v: int) -> int:
        if v < 1:
            raise ValueError("useful_life must be >= 1")
        return v

    @field_validator("start_month")
    @classmethod
    def valid_month(cls, v: int) -> int:
        if not 1 <= v <= 12:
            raise ValueError("start_month must be between 1 and 12")
        return v


class InvestmentCreate(InvestmentBase):
    pass


class InvestmentUpdate(BaseModel):
    investment_category_id: int | None = None
    asset_code: str | None = None
    asset_name: str | None = None
    purchase_price: float | None = None
    bos: float | None = None
    useful_life: int | None = None
    start_month: int | None = None


class InvestmentRead(InvestmentBase):
    id: int
    organization_id: int
    dep_per_year: float
    dep_current_year: float
    end_book_value: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
