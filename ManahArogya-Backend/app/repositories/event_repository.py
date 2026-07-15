from sqlmodel import Session, select

from app.database.models import Event, EventRegistration


class EventRepository:
    """Database operations for events and registrations."""

    def __init__(self, session: Session) -> None:
        """Store the active database session."""
        self.session = session

    def list_events(self) -> list[Event]:
        """Return all events."""
        return list(self.session.exec(select(Event)))

    def get_event(self, event_id: int) -> Event | None:
        """Return one event by ID."""
        statement = select(Event).where(Event.id == event_id)
        return self.session.exec(statement).first()

    def save_event(self, event: Event) -> Event:
        """Persist event updates."""
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return event

    def create_registration(self, registration: EventRegistration) -> EventRegistration:
        """Insert a new event registration."""
        self.session.add(registration)
        self.session.commit()
        self.session.refresh(registration)
        return registration

    def ensure_seed_data(self) -> None:
        """Populate starter events if table is empty."""
        if self.list_events():
            return
        starter_events = [
            Event(
                title="Stress Reset Workshop",
                description="Practical tools for managing stress during exams.",
                category="workshop",
                date="Friday",
                time="6:00 PM",
                mode="Online",
                host="Wellness Team",
                capacity=40,
                attendees=12,
            ),
            Event(
                title="Peer Support Circle",
                description="Small-group check-in circle with guided prompts.",
                category="community-circle",
                date="Saturday",
                time="5:00 PM",
                mode="Community Hall",
                host="Peer Mentors",
                capacity=30,
                attendees=20,
            ),
        ]
        for event in starter_events:
            self.session.add(event)
        self.session.commit()
