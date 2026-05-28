"""
Pydantic schemas untuk autentikasi dan manajemen user.
"""
from pydantic import BaseModel


class Token(BaseModel):
    """Response dari endpoint login."""
    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    """Data user yang dikembalikan ke client (tanpa password)."""
    id: int
    username: str
    role: str
    org_id: int | None
    is_active: bool

    model_config = {"from_attributes": True}


class PasswordResetResponse(BaseModel):
    """Response setelah reset password org user."""
    username: str
    new_password: str
