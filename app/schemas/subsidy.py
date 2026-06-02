"""
Pydantic schemas untuk subsidi dari Cabang/Pusat ke unit penerima (Subsidy).
"""
from pydantic import BaseModel


class SubsidyBase(BaseModel):
    recipient_org_id: int
    expense_category_id: int
    income_category_id: int
    amount: float = 0.0
    is_active: bool = True


class SubsidyCreate(SubsidyBase):
    pass


class SubsidyUpdate(BaseModel):
    recipient_org_id: int | None = None
    expense_category_id: int | None = None
    income_category_id: int | None = None
    amount: float | None = None
    is_active: bool | None = None


class SubsidyRead(SubsidyBase):
    id: int
    provider_org_id: int
    recipient_org_name: str | None = None
    expense_category_code: str | None = None
    expense_category_label: str | None = None
    income_category_code: str | None = None
    income_category_label: str | None = None

    model_config = {"from_attributes": True}
