from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    """Payload for login or user bootstrap."""

    token: str | None = None
    uid: str | None = None
    email: str | None = None
    name: str | None = None


class UserResponse(BaseModel):
    """User details returned by APIs."""

    id: int
    external_uid: str
    email: str | None
    name: str | None
    role: str = "user"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    """Login payload with onboarding state."""

    user: UserResponse
    has_completed_assessment: bool = False
    risk_level: str = "low"
