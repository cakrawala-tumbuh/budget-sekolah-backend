"""
Pydantic schemas untuk konfigurasi alokasi biaya dari Cabang/Pusat ke unit anak
(ParentExpenseAllocation).
"""
from pydantic import BaseModel


class ParentExpenseAllocationBase(BaseModel):
    expense_category_id: int
    affects_up: bool = False
    is_active: bool = True


class ParentExpenseAllocationCreate(ParentExpenseAllocationBase):
    pass


class ParentExpenseAllocationUpdate(BaseModel):
    affects_up: bool | None = None
    is_active: bool | None = None


class ParentExpenseAllocationRead(ParentExpenseAllocationBase):
    id: int
    parent_org_id: int
    expense_category_code: str | None = None
    expense_category_label: str | None = None

    model_config = {"from_attributes": True}
