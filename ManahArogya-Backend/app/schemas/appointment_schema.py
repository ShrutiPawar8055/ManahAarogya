from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AppointmentBookRequest(BaseModel):
    """Payload to book an appointment."""

    counselor_name: str | None = None
    therapist_id: int
    preferred_slot: str | None = None
    start_time: str
    end_time: str
    mode: str = "Online"
    location: str | None = None
    notes: str | None = None


class RescheduleRequest(BaseModel):
    """Payload to reschedule an appointment."""

    preferred_slot: str


class AppointmentResponse(BaseModel):
    """Appointment response schema."""

    id: int
    user_id: int
    therapist_id: int | None = None
    counselor_name: str | None = None
    preferred_slot: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    mode: str
    location: str | None = None
    notes: str | None = None
    therapist_notes: str | None = None
    status: str
    google_event_id: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
