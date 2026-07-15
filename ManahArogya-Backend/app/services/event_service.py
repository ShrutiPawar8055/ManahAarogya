from fastapi import Depends, HTTPException
from sqlmodel import Session

from app.database.db import get_session
from app.database.models import EventRegistration
from app.repositories.event_repository import EventRepository


class EventService:
    """Business logic for events."""

    def __init__(self, session: Session) -> None:
        """Create service with repository dependencies."""
        self.event_repository = EventRepository(session)

    def list_events(self, category: str | None) -> dict[str, object]:
        """Return events grouped for UI needs."""
        events = self.event_repository.list_events()
        if category:
            events = [item for item in events if item.category == category]
        featured = events[0] if events else None
        return {"featured": featured, "upcoming": events, "weekly_lineup": events[:5]}

    def register(self, user_id: int, event_id: int, mode: str):
        """Register user for an event."""
        event = self.event_repository.get_event(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found.")
        registration = EventRegistration(user_id=user_id, event_id=event_id, mode=mode)
        self.event_repository.create_registration(registration)
        if mode == "reserve":
            event.attendees += 1
            self.event_repository.save_event(event)
        return event


def get_event_service(session: Session = Depends(get_session)) -> EventService:
    """FastAPI dependency for EventService."""
    return EventService(session)
