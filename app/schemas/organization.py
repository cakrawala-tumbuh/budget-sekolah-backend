"""
Pydantic schemas untuk entitas organisasi.

OrganizationCreate digunakan pada POST, OrganizationUpdate pada PUT.
Kode organisasi secara otomatis dinormalisasi ke uppercase.
OrganizationReadWithChildren menyertakan daftar anak langsung (satu level).
"""
from datetime import datetime

from pydantic import BaseModel, field_validator

from ..models.organization import OrgType


class OrganizationBase(BaseModel):
    code: str
    name: str
    org_type: OrgType
    city: str | None = None
    # Saldo kas & setara kas awal organisasi (total saja, tanpa rincian)
    cash_balance: float = 0.0
    parent_id: int | None = None

    @field_validator("code")
    @classmethod
    def code_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("code must not be empty")
        return v.strip().upper()


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: str | None = None
    city: str | None = None
    cash_balance: float | None = None
    parent_id: int | None = None


class OrganizationCashBalanceUpdate(BaseModel):
    """Schema untuk update saldo kas & setara kas saja (boleh oleh user org)."""
    cash_balance: float


class OrganizationRead(OrganizationBase):
    id: int
    is_locked: bool
    locked_at: datetime | None
    locked_by_username: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrganizationCreated(OrganizationRead):
    """Schema untuk response POST /organizations — menyertakan password awal sekali."""
    generated_password: str


class OrganizationReadWithChildren(OrganizationRead):
    children: list[OrganizationRead] = []


class OrganizationPasswordReset(BaseModel):
    """Schema untuk response POST /organizations/{org_id}/reset-password."""
    org_id: int
    username: str
    new_password: str
