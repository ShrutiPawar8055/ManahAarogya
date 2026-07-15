from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime

from app.database.db import get_session
from app.database.models import Appointment, Therapist, User
from app.services.assessment_service import AssessmentService
from app.services.auth_service import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/therapist", tags=["therapist_dashboard"])

def get_current_therapist(
    user=Depends(get_current_user), session: Session = Depends(get_session)
):
    """Dependency to ensure the user is a verified therapist and load their profile."""
    if user.role != "therapist":
        raise HTTPException(status_code=403, detail="Access denied. Therapist role required.")
    
    therapist = session.exec(select(Therapist).where(Therapist.user_id == user.id)).first()
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist profile not found.")
    return therapist

class AppointmentStatusUpdate(BaseModel):
    status: str

class AppointmentNotesUpdate(BaseModel):
    therapist_notes: str


@router.get("/stats")
def therapist_stats(therapist: Therapist = Depends(get_current_therapist), session: Session = Depends(get_session)):
    """Get overview metrics for the therapist dashboard."""
    appointments = session.exec(select(Appointment).where(Appointment.therapist_id == therapist.id)).all()
    
    today_date = datetime.utcnow().date().isoformat()
    sessions_today = sum(1 for a in appointments if a.start_time and a.start_time.startswith(today_date) and a.status != "cancelled")
    pending_requests = sum(1 for a in appointments if a.status == "pending")
    
    # Active patients = unique users with non-cancelled appointments
    active_patient_ids = set([a.user_id for a in appointments if a.status not in ("cancelled",)])
    
    return {
        "data": {
            "sessions_today": sessions_today,
            "pending_requests": pending_requests,
            "active_patients": len(active_patient_ids),
            "total_appointments": len(appointments)
        }
    }


@router.get("/appointments")
def list_appointments(
    status: str | None = None,
    therapist: Therapist = Depends(get_current_therapist), 
    session: Session = Depends(get_session)
):
    """List all appointments for this therapist."""
    query = select(Appointment).where(Appointment.therapist_id == therapist.id)
    if status:
        query = query.where(Appointment.status == status)
    
    appointments = session.exec(query).all()
    
    # Attach basic user details (like name/email) for display purposes
    results = []
    for appt in appointments:
        user = session.get(User, appt.user_id)
        appt_dict = dict(appt)
        appt_dict["patient_name"] = user.name if user else "Unknown"
        appt_dict["patient_email"] = user.email if user else "Unknown"
        results.append(appt_dict)
        
    return {"data": results}


@router.patch("/appointments/{appointment_id}/status")
def update_status(
    appointment_id: int, 
    payload: AppointmentStatusUpdate,
    therapist: Therapist = Depends(get_current_therapist), 
    session: Session = Depends(get_session)
):
    """Accept, decline, cancel or complete an appointment."""
    appointment = session.get(Appointment, appointment_id)
    if not appointment or appointment.therapist_id != therapist.id:
        raise HTTPException(status_code=404, detail="Appointment not found or access denied.")
    
    appointment.status = payload.status
    session.add(appointment)
    session.commit()
    session.refresh(appointment)
    return {"data": appointment}


@router.patch("/appointments/{appointment_id}/notes")
def update_notes(
    appointment_id: int, 
    payload: AppointmentNotesUpdate,
    therapist: Therapist = Depends(get_current_therapist), 
    session: Session = Depends(get_session)
):
    """Save private therapist observations/notes for a session."""
    appointment = session.get(Appointment, appointment_id)
    if not appointment or appointment.therapist_id != therapist.id:
        raise HTTPException(status_code=404, detail="Appointment not found or access denied.")
    
    appointment.therapist_notes = payload.therapist_notes
    session.add(appointment)
    session.commit()
    return {"data": appointment}


class ChatMessagePayload(BaseModel):
    content: str
    message_type: str = "text"
    resource_id: str | None = None


@router.get("/patients")
def list_patients(therapist: Therapist = Depends(get_current_therapist), session: Session = Depends(get_session)):
    """Get all unique patients assigned to this therapist."""
    appointments = session.exec(select(Appointment).where(Appointment.therapist_id == therapist.id)).all()
    patient_ids = {a.user_id for a in appointments}
    
    patients = []
    for pid in patient_ids:
        user = session.get(User, pid)
        if user:
            user_appts = [a for a in appointments if a.user_id == pid]
            last_appt = max(user_appts, key=lambda x: x.created_at) if user_appts else None
            patients.append({
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "last_session": last_appt.start_time if last_appt else None,
                "status": last_appt.status if last_appt else "unknown"
            })
    return {"data": patients}


@router.get("/patients/{user_id}")
def patient_details(user_id: int, therapist: Therapist = Depends(get_current_therapist), session: Session = Depends(get_session)):
    """Get rich history for a specific patient."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    appts = session.exec(select(Appointment).where(Appointment.therapist_id == therapist.id, Appointment.user_id == user_id)).all()
    
    assessment_service = AssessmentService(session)

    return {
        "data": {
            "profile": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "joined": user.created_at
            },
            "appointments": appts,
            "assessment_history": assessment_service.list_history(user_id, limit=6),
        }
    }


@router.get("/patients/{user_id}/insights")
def patient_ai_insights(user_id: int, therapist: Therapist = Depends(get_current_therapist), session: Session = Depends(get_session)):
    """Return structured therapist-facing insight data based on the latest assessment session."""
    assessment_service = AssessmentService(session)
    latest_session = assessment_service.latest_session(user_id)

    if not latest_session:
        return {
            "data": {
                "summary": "No completed assessment session is available for this patient yet.",
                "bullet_points": ["Ask the patient to complete an assessment to unlock structured analysis."],
                "risk_level": "Unknown",
                "suggested_topics": ["baseline screening"],
            }
        }

    feedback = latest_session.get("feedback", {})
    return {
        "data": {
            "summary": feedback.get("overall_summary") or "No AI summary available.",
            "bullet_points": feedback.get("key_findings") or ["No key findings available."],
            "risk_level": feedback.get("risk_level") or latest_session.get("risk_level") or "low",
            "suggested_topics": feedback.get("suggested_topics") or feedback.get("follow_up_questions") or ["symptom review"],
            "clinician_flags": feedback.get("clinician_flags") or [],
        }
    }


@router.get("/chat/{user_id}")
def get_chat(user_id: int, therapist: Therapist = Depends(get_current_therapist), session: Session = Depends(get_session)):
    """Retrieve secure messaging history."""
    from app.database.models import TherapistMessage
    messages = session.exec(
        select(TherapistMessage)
        .where(TherapistMessage.therapist_id == therapist.id, TherapistMessage.user_id == user_id)
        .order_by(TherapistMessage.created_at.asc())
    ).all()
    return {"data": messages}


@router.post("/chat/{user_id}")
def send_chat(user_id: int, payload: ChatMessagePayload, therapist: Therapist = Depends(get_current_therapist), session: Session = Depends(get_session)):
    """Dispatch a secure message or resource to the patient."""
    from app.database.models import TherapistMessage
    
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    msg = TherapistMessage(
        therapist_id=therapist.id,
        user_id=user_id,
        sender="therapist",
        content=payload.content,
        message_type=payload.message_type,
        resource_id=payload.resource_id
    )
    session.add(msg)
    session.commit()
    session.refresh(msg)
    return {"data": msg}
