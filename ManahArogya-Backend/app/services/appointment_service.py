from fastapi import Depends, HTTPException
from sqlmodel import Session

from datetime import datetime, timedelta

from app.database.db import get_session
from app.database.models import Appointment, Therapist, User
from app.repositories.appointment_repository import AppointmentRepository
from app.services.google_calendar_service import fetch_free_busy, create_calendar_event
from sqlmodel import select


class AppointmentService:
    """Business logic for counseling appointments."""

    def __init__(self, session: Session) -> None:
        """Create service with repository dependencies."""
        self.session = session
        self.appointment_repository = AppointmentRepository(session)

    def list_appointments(self, user_id: int) -> list[dict[str, object]]:
        """Return user appointments."""
        appointments = self.appointment_repository.list_by_user(user_id)
        payload: list[dict[str, object]] = []
        for item in appointments:
            slot = item.preferred_slot or ""
            parts = slot.split(" ")
            payload.append(
                {
                    "id": item.id,
                    "doctor": item.counselor_name,
                    "counselor_name": item.counselor_name,
                    "specialty": "Wellness Counseling",
                    "date": parts[0] if parts else slot,
                    "time": " ".join(parts[1:]) if len(parts) > 1 else slot,
                    "preferred_slot": item.preferred_slot,
                    "mode": item.mode,
                    "status": item.status,
                    "notes": item.notes,
                }
            )
        return payload

    def book(self, user_id: int, therapist_id: int, counselor_name: str | None, preferred_slot: str | None, start_time: str, end_time: str, mode: str, location: str | None, notes: str | None) -> Appointment:
        """Book a new appointment."""
        appointment = Appointment(
            user_id=user_id,
            therapist_id=therapist_id,
            counselor_name=counselor_name,
            preferred_slot=preferred_slot,
            start_time=start_time,
            end_time=end_time,
            mode=mode,
            location=location,
            notes=notes,
            status="pending"
        )
        saved = self.appointment_repository.create(appointment)
        
        # Try finding the user and therapist to fetch emails
        user = self.session.get(User, user_id)
        therapist = self.session.get(Therapist, therapist_id)
        therapist_user = self.session.get(User, therapist.user_id) if therapist and therapist.user_id else None
        
        user_email = user.email if user and user.email else "patient@example.com"
        therapist_email = therapist_user.email if therapist_user and therapist_user.email else "therapist@example.com"
        
        event_id = create_calendar_event(
            therapist_email=therapist_email,
            user_email=user_email,
            start_time=start_time,
            end_time=end_time,
            summary=f"Therapy Session: {user.name if user and user.name else 'Patient'}",
            description=notes or "Routine therapy session."
        )
        if event_id:
            saved.google_event_id = event_id
            self.session.add(saved)
            self.session.commit()
            self.session.refresh(saved)
            
        return saved

    def reschedule(self, user_id: int, appointment_id: int, preferred_slot: str) -> Appointment:
        """Reschedule an existing appointment."""
        appointment = self.appointment_repository.get_by_id(user_id, appointment_id)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found.")
        appointment.preferred_slot = preferred_slot
        appointment.status = "rescheduled"
        return self.appointment_repository.save(appointment)

    def stats(self, user_id: int) -> dict[str, int]:
        """Return appointment counts by status."""
        appointments = self.appointment_repository.list_by_user(user_id)
        booked = sum(1 for item in appointments if item.status == "booked")
        rescheduled = sum(1 for item in appointments if item.status == "rescheduled")
        return {"total": len(appointments), "booked": booked, "rescheduled": rescheduled}

    def counselors(self) -> list[dict[str, object]]:
        """Return therapist directory from database."""
        therapists = self.session.exec(select(Therapist).where(Therapist.is_verified == True)).all()
        return [
            {
                "id": t.id,
                "name": t.name,
                "specialty": t.specialty,
                "session_duration": t.session_duration,
                "region": t.region,
                "institution": t.institution
            }
            for t in therapists
        ]

    def open_slots(self, therapist_id: int, date_str: str) -> list[dict]:
        """Return available appointment slots checking against Google Calendar Free/Busy."""
        therapist = self.session.get(Therapist, therapist_id)
        if not therapist:
            return []
            
        therapist_user = self.session.get(User, therapist.user_id) if therapist.user_id else None
        therapist_email = therapist_user.email if therapist_user and therapist_user.email else "therapist@example.com"
            
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return []
            
        time_min = datetime.combine(target_date, datetime.min.time())
        time_max = datetime.combine(target_date, datetime.max.time())
        
        busy_spans = fetch_free_busy(therapist_email, time_min, time_max)
        
        # Parse busy periods into naive datetimes for easy comparison
        busy_times = []
        for span in busy_spans:
            b_start = datetime.fromisoformat(span['start'].replace('Z', '+00:00')).replace(tzinfo=None)
            b_end = datetime.fromisoformat(span['end'].replace('Z', '+00:00')).replace(tzinfo=None)
            busy_times.append((b_start, b_end))
            
        # Generate 1-hour slots from 9AM to 5PM UTC
        open_slots = []
        duration = timedelta(minutes=therapist.session_duration)
        current_time = datetime.combine(target_date, datetime.min.time().replace(hour=9))
        end_time = datetime.combine(target_date, datetime.min.time().replace(hour=17))
        
        while current_time + duration <= end_time:
            slot_end = current_time + duration
            # Check overlap
            overlap = False
            for (b_start, b_end) in busy_times:
                if (current_time < b_end) and (slot_end > b_start):
                    overlap = True
                    break
            
            if not overlap:
                open_slots.append({
                    "start": current_time.isoformat() + "Z",
                    "end": slot_end.isoformat() + "Z",
                    "display": current_time.strftime("%I:%M %p")
                })
            
            current_time += duration
            
        return open_slots

    def prep_checklist(self) -> list[str]:
        """Return pre-appointment checklist."""
        return ["Bring key concerns", "Carry any medications list", "Join 5 minutes early"]


def get_appointment_service(session: Session = Depends(get_session)) -> AppointmentService:
    """FastAPI dependency for AppointmentService."""
    return AppointmentService(session)
