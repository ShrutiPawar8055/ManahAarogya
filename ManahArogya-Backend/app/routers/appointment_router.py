from fastapi import APIRouter, Depends

from app.schemas.appointment_schema import AppointmentBookRequest, RescheduleRequest
from app.services.appointment_service import AppointmentService, get_appointment_service
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.get("/stats")
def stats(user=Depends(get_current_user), service: AppointmentService = Depends(get_appointment_service)):
    """Return appointment statistics."""
    return {"data": service.stats(user.id)}


@router.get("/counselors")
def counselors(_user=Depends(get_current_user), service: AppointmentService = Depends(get_appointment_service)):
    """Return counselor list."""
    return {"data": service.counselors()}


@router.get("/upcoming")
def upcoming(user=Depends(get_current_user), service: AppointmentService = Depends(get_appointment_service)):
    """Return user appointments."""
    return {"data": service.list_appointments(user.id)}


@router.get("/open-slots")
def open_slots(
    therapist_id: int,
    date: str,
    _user=Depends(get_current_user), 
    service: AppointmentService = Depends(get_appointment_service)
):
    """Return open appointment slots for a specific therapist on a given date."""
    return {"data": service.open_slots(therapist_id, date)}


@router.get("/prep-checklist")
def prep_checklist(_user=Depends(get_current_user), service: AppointmentService = Depends(get_appointment_service)):
    """Return pre-appointment checklist."""
    return {"data": service.prep_checklist()}


@router.post("/book")
def book(payload: AppointmentBookRequest, user=Depends(get_current_user), service: AppointmentService = Depends(get_appointment_service)):
    """Book a new appointment."""
    appointment = service.book(
        user.id,
        payload.therapist_id,
        payload.counselor_name,
        payload.preferred_slot,
        payload.start_time,
        payload.end_time,
        payload.mode,
        payload.location,
        payload.notes,
    )
    return {"data": appointment, "appointment": appointment}


@router.post("/{appointment_id}/reschedule")
def reschedule(appointment_id: int, payload: RescheduleRequest, user=Depends(get_current_user), service: AppointmentService = Depends(get_appointment_service)):
    """Reschedule an appointment."""
    appointment = service.reschedule(user.id, appointment_id, payload.preferred_slot)
    return {"data": appointment, "appointment": appointment}
