from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HabitCreateRequest(BaseModel):
    """Payload to create a habit."""

    title: str
    description: str | None = None
    schedule: str = "Anytime"
    category: str = "wellbeing"


class HabitUpdateRequest(BaseModel):
    """Payload to update a habit."""

    title: str | None = None
    description: str | None = None
    schedule: str | None = None
    category: str | None = None
    done: bool | None = None


class HabitCoachRequest(BaseModel):
    """Payload for habit coaching chat."""

    message: str | None = None


class HabitOnboardingSubmitRequest(BaseModel):
    """Payload for first-time habit onboarding answers."""

    answers: dict[str, str]


class HabitResponse(BaseModel):
    """Habit data returned by APIs."""

    id: int
    user_id: int
    title: str
    description: str | None
    schedule: str
    category: str
    done: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
