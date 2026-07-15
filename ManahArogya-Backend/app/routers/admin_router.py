from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.core.logging import logger
from app.database.db import get_session
from app.database.models import Alert, CommunityCommentReddit, CommunityPostReddit, Event, Resource, Therapist, User
from app.schemas.admin_schema import (
    AlertResponse,
    BanRequest,
    EventAdminCreateRequest,
    EventResponse,
    ResolveAlertRequest,
    ResourceAdminCreateRequest,
    ResourceResponse,
    RoleUpdateRequest,
    TherapistCreateRequest,
    TherapistResponse,
    UserAdminResponse,
)
from app.services.assessment_service import AssessmentService
from app.services.auth_service import get_admin_user

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=list[UserAdminResponse])
def get_all_users(
    organization: str | None = Query(default=None),
    _admin_user=Depends(get_admin_user),
    session: Session = Depends(get_session),
):
    """Retrieve all users, optionally filtered by organization. Ignores incomplete/N/A users."""
    query = select(User).where(User.name.isnot(None), User.name != "", User.name != "N/A")
    if organization:
        query = query.where(User.organization == organization)
    users = session.exec(query).all()
    return users


@router.get("/users/{user_id}/summary")
def get_user_summary(
    user_id: int,
    _admin_user=Depends(get_admin_user),
    session: Session = Depends(get_session),
):
    """Get session-aware assessment summary for a user."""
    assessment_service = AssessmentService(session)
    return {
        "user_id": user_id,
        "assessments": assessment_service.list_history(user_id, limit=10),
        "latest_assessment": assessment_service.latest_session(user_id),
    }


@router.patch("/users/{user_id}/ban")
def update_user_ban_status(
    user_id: int,
    payload: BanRequest,
    _admin_user=Depends(get_admin_user),
    session: Session = Depends(get_session),
):
    """Ban or unban a user."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.is_banned = payload.is_banned
    session.add(user)
    session.commit()
    return {"status": "success", "is_banned": user.is_banned}


@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    payload: RoleUpdateRequest,
    _admin_user=Depends(get_admin_user),
    session: Session = Depends(get_session),
):
    """Update user role and organization."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.role = payload.role
    user.organization = payload.organization
    session.add(user)
    session.commit()
    return {"status": "success", "role": user.role, "organization": user.organization}


@router.get("/posts")
def get_all_posts(
    flagged_only: bool = Query(default=False),
    _admin_user=Depends(get_admin_user),
    session: Session = Depends(get_session),
):
    """Get community posts, optionally filtering for flagged ones."""
    query = select(CommunityPostReddit)
    if flagged_only:
        query = query.where(CommunityPostReddit.is_flagged == True)
    posts = session.exec(query).all()
    return posts


@router.patch("/posts/{post_id}/approve")
def approve_post(
    post_id: int,
    _admin_user=Depends(get_admin_user),
    session: Session = Depends(get_session),
):
    """Approve a post and remove its flag."""
    post = session.get(CommunityPostReddit, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    post.is_approved = True
    post.is_flagged = False
    session.add(post)
    session.commit()
    return {"status": "success"}


@router.delete("/posts/{post_id}")
def delete_post(
    post_id: int,
    _admin_user=Depends(get_admin_user),
    session: Session = Depends(get_session),
):
    """Permanently delete a post."""
    post = session.get(CommunityPostReddit, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    session.delete(post)
    session.commit()
    return {"status": "deleted"}


@router.get("/therapists", response_model=list[TherapistResponse])
def get_therapists(
    _admin_user=Depends(get_admin_user),
    session: Session = Depends(get_session),
):
    """Get all therapists."""
    return session.exec(select(Therapist)).all()


@router.post("/therapists", response_model=TherapistResponse)
def create_therapist(
    payload: TherapistCreateRequest,
    _admin_user=Depends(get_admin_user),
    session: Session = Depends(get_session),
):
    """Create a new therapist."""
    therapist = Therapist(**payload.model_dump())
    session.add(therapist)
    session.commit()
    session.refresh(therapist)
    return therapist


@router.delete("/therapists/{therapist_id}")
def delete_therapist(
    therapist_id: int,
    _admin_user=Depends(get_admin_user),
    session: Session = Depends(get_session),
):
    """Delete a therapist."""
    therapist = session.get(Therapist, therapist_id)
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found.")
    session.delete(therapist)
    session.commit()
    return {"status": "deleted"}


@router.get("/alerts", response_model=list[AlertResponse])
def get_alerts(
    resolved: bool | None = Query(default=None),
    _admin_user=Depends(get_admin_user),
    session: Session = Depends(get_session),
):
    """Get system alerts (e.g. suicidal language detection)."""
    query = select(Alert)
    if resolved is not None:
        query = query.where(Alert.is_resolved == resolved)
    return session.exec(query).all()


@router.patch("/alerts/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    payload: ResolveAlertRequest,
    _admin_user=Depends(get_admin_user),
    session: Session = Depends(get_session),
):
    """Mark an alert as resolved."""
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    alert.is_resolved = payload.is_resolved
    session.add(alert)
    session.commit()
    return {"status": "success", "is_resolved": alert.is_resolved}


@router.post("/resources", response_model=ResourceResponse)
def create_resource(
    payload: ResourceAdminCreateRequest,
    _admin_user=Depends(get_admin_user),
    session: Session = Depends(get_session),
):
    """Create a new resource."""
    resource = Resource(**payload.model_dump())
    session.add(resource)
    session.commit()
    session.refresh(resource)
    return resource


@router.delete("/resources/{resource_id}")
def delete_resource(
    resource_id: int,
    _admin_user=Depends(get_admin_user),
    session: Session = Depends(get_session),
):
    """Delete a resource."""
    resource = session.get(Resource, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found.")
    session.delete(resource)
    session.commit()
    return {"status": "deleted"}


@router.post("/events", response_model=EventResponse)
def create_event(
    payload: EventAdminCreateRequest,
    _admin_user=Depends(get_admin_user),
    session: Session = Depends(get_session),
):
    """Create a new event."""
    event = Event(**payload.model_dump(), attendees=0)
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


@router.delete("/events/{event_id}")
def delete_event(
    event_id: int,
    _admin_user=Depends(get_admin_user),
    session: Session = Depends(get_session),
):
    """Delete an event."""
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")
    session.delete(event)
    session.commit()
    return {"status": "deleted"}
