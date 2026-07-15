from pydantic import BaseModel, Field


class MoodLogRequest(BaseModel):
    """Request payload for logging user mood."""

    mood_score: int = Field(ge=1, le=10)
    notes: str | None = None
