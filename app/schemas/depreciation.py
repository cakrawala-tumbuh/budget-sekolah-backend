"""
Pydantic schemas untuk aset tetap lama yang masih disusutkan.

Digunakan di endpoint POST/PUT /organizations/{org_id}/depreciation.
Depresiasi garis lurus: dep_per_year = acquisition_cost / useful_life.
"""
from datetime import datetime

from pydantic import BaseModel, field_validator


class DepreciationOldAssetBase(BaseModel):
    asset_code: str | None = None
    asset_name: str
    acquisition_cost: float
    useful_life: int
    acquisition_year: int

    @field_validator("acquisition_cost")
    @classmethod
    def positive_value(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("acquisition_cost must be > 0")
        return v

    @field_validator("useful_life")
    @classmethod
    def positive_life(cls, v: int) -> int:
        if v < 1:
            raise ValueError("useful_life must be >= 1")
        return v

    @field_validator("acquisition_year")
    @classmethod
    def valid_year(cls, v: int) -> int:
        if v < 1900 or v > 2100:
            raise ValueError("acquisition_year is not valid")
        return v


class DepreciationOldAssetCreate(DepreciationOldAssetBase):
    pass


class DepreciationOldAssetUpdate(BaseModel):
    asset_code: str | None = None
    asset_name: str | None = None
    acquisition_cost: float | None = None
    useful_life: int | None = None
    acquisition_year: int | None = None


class DepreciationOldAssetRead(DepreciationOldAssetBase):
    id: int
    organization_id: int
    dep_per_year: float
    dep_current_year: float
    book_value: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
