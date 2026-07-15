from sqlmodel import Session, select

from app.database.models import Appointment


class AppointmentRepository:
    """Database operations for appointments."""

    def __init__(self, session: Session) -> None:
        """Store the active database session."""
        self.session = session

    def list_by_user(self, user_id: int) -> list[Appointment]:
        """Return all appointments for a user."""
        statement = select(Appointment).where(Appointment.user_id == user_id)
        rows = list(self.session.exec(statement))
        return sorted(rows, key=lambda item: item.created_at, reverse=True)

    def get_by_id(self, user_id: int, appointment_id: int) -> Appointment | None:
        """Return one appointment scoped to user."""
        statement = select(Appointment).where(
            Appointment.user_id == user_id,
            Appointment.id == appointment_id,
        )
        return self.session.exec(statement).first()

    def create(self, appointment: Appointment) -> Appointment:
        """Insert a new appointment."""
        self.session.add(appointment)
        self.session.commit()
        self.session.refresh(appointment)
        return appointment

    def save(self, appointment: Appointment) -> Appointment:
        """Persist updates to an appointment."""
        self.session.add(appointment)
        self.session.commit()
        self.session.refresh(appointment)
        return appointment
