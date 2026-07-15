from fastapi import APIRouter, Depends, Query

from app.services.auth_service import get_current_user
from app.services.event_service import EventService, get_event_service

router = APIRouter(prefix="/events", tags=["events"])


@router.get("")
@router.get("/")
def list_events(category: str | None = Query(default=None), _user=Depends(get_current_user), service: EventService = Depends(get_event_service)):
    """Return events grouped for client screens."""
    payload = service.list_events(category)
    return {
        "data": payload,
        "featured": payload.get("featured"),
        "upcoming": payload.get("upcoming", []),
        "weekly_lineup": payload.get("weekly_lineup", []),
    }


@router.post("/{event_id}/reserve")
def reserve(event_id: int, user=Depends(get_current_user), service: EventService = Depends(get_event_service)):
    """Reserve a seat for an event."""
    event = service.register(user.id, event_id, "reserve")
    return {"data": {"event": event}, "event": event}


@router.post("/{event_id}/waitlist")
def waitlist(event_id: int, user=Depends(get_current_user), service: EventService = Depends(get_event_service)):
    """Join waitlist for an event."""
    event = service.register(user.id, event_id, "waitlist")
    return {"data": {"event": event}, "event": event}
