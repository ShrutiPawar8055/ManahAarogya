from pydantic import BaseModel, ConfigDict


class EventResponse(BaseModel):
    """Event response schema."""

    id: int
    title: str
    description: str
    category: str
    date: str
    time: str
    mode: str
    host: str
    capacity: int
    attendees: int

    model_config = ConfigDict(from_attributes=True)
