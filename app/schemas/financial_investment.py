"""Pydantic schemas untuk investasi keuangan CABANG/PUSAT."""
from datetime import datetime

from pydantic import BaseModel, field_validator

from ..models.financial_investment import InstrumentType


class FinancialInvestmentBase(BaseModel):
    instrument_type: InstrumentType
    name: str
    amount: float
    notes: str | None = None

    @field_validator("amount")
    @classmethod
    def positive_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("amount must be > 0")
        return v


class FinancialInvestmentCreate(FinancialInvestmentBase):
    pass


class FinancialInvestmentUpdate(BaseModel):
    instrument_type: InstrumentType | None = None
    name: str | None = None
    amount: float | None = None
    notes: str | None = None


class FinancialInvestmentRead(FinancialInvestmentBase):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
